// Testing Setup Module in Schools
QUnit.module('schools');

// Testing setting Courses
QUnit.test('test course', function(assert) {
	assert.expect(8);
	let done = assert.async();
	frappe.run_serially([
		() => {
			return frappe.tests.make('Course', [
				{course_name: 'Test_Subject'},
				{course_code: 'Test_Sub'},
				{department: 'Teaching'},
				{course_abbreviation: 'Test_Sub'},
				{course_intro: 'Test Subject Intro'},
				{default_grading_scale: 'GTU'},
				{assessment_criteria: [
					[
						{assessment_criteria: 'Pass'},
						{weightage: 100}
					]
				]}
			]);
		},
		() => cur_frm.save(),
		() => frappe.timeout(1),
		() => {
			assert.ok(cur_frm.doc.course_name == 'Test_Subject');
			assert.ok(cur_frm.doc.course_code == 'Test_Sub');
			assert.ok(cur_frm.doc.department == 'Teaching');
			assert.ok(cur_frm.doc.course_abbreviation == 'Test_Sub');
			assert.ok(cur_frm.doc.course_intro == 'Test Subject Intro');
			assert.ok(cur_frm.doc.default_grading_scale == 'GTU');
			assert.ok(cur_frm.doc.assessment_criteria[0].assessment_criteria == 'Pass');
			assert.ok(cur_frm.doc.assessment_criteria[0].weightage == '100');
		},
		() => done()
	]);
});