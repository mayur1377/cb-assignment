from frappe.model.document import Document


class CBIssueType(Document):
	def before_save(self):
		parts = [self.department, self.category, self.sub_category_1, self.sub_category_2]
		self.title = " / ".join([p for p in parts if p])
