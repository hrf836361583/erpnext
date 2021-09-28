# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime
from erpnext.hr.doctype.interview.interview import update_rating

class UnexpectedSkillError(frappe.ValidationError):
	pass

class InterviewFeedback(Document):
	def validate(self):
		self.calculate_average_rating()
		self.validate_interviewer()
		self.validate_interview_date()
		self.validate_duplicate()
		self.validate_skills()

	def validate_interviewer(self):
		applicable_interviewers = get_applicable_interviewers(self.interview)
		if self.interviewer not in applicable_interviewers:
			frappe.throw(_("{0} is not allowed to submit Interview Feedback for Interview: {1}").format(frappe.bold(self.interviewer), frappe.bold(self.interview)))

	def validate_interview_date(self):
		scheduled_date = get_datetime(frappe.db.get_value("Interview", self.interview, "scheduled_on"))
		if get_datetime() < scheduled_date and self.docstatus == 1:
			frappe.throw(_("{0} submission before {1} is not allowed").format(
				frappe.bold("Interview Feedback"),
				frappe.bold("Interview Scheduled Date")
			))

	def validate_duplicate(self):
		duplicate_feedback = frappe.db.exists("Interview Feedback", {
			"interviewer": self.interviewer,
			"interview": self.interview,
			"docstatus": 1
		})

		if duplicate_feedback:
			frappe.throw(_("Interviewers are not allowed to submit Interview Feedback twice. Please cancel previous Interview Feedback"))

	def validate_skills(self):
		skills = frappe.get_all("Expected Skill Set", filters={"parent": self.interview_round}, fields = ["skill"])
		skills = [d.skill for d in skills]

		if skills != [d.skill for d in self.skill_assessment]:
			frappe.throw(_("Only Expected skills from Interview Round: {0} are allowed to rate").format(self.interview_round), exc = UnexpectedSkillError)

	def calculate_average_rating(self):
		total_rating = 0
		for d in self.skill_assessment:
			if d.rating:
				total_rating += d.rating

		avg_rating = total_rating/len(self.skill_assessment) if len(self.skill_assessment) else 1

		self.average_rating = avg_rating
		self.average_rating_value = avg_rating


	def on_submit(self):
		self.set_interview_average_rating()

	def set_interview_average_rating(self):
		update_rating(self.interview, self.interviewer, self.name, self.feedback, self.average_rating)

	def before_cancel(self):
		update_rating(self.interview, self.interviewer, revert=0)

@frappe.whitelist()
def get_applicable_interviewers(interview):
	data = frappe.get_all("Interview Detail", filters= {"parent": interview}, fields =["interviewer"])
	return [d.interviewer for d in data]
