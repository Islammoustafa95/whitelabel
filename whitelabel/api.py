from __future__ import unicode_literals
import frappe
import json
from frappe.utils import floor, flt, today, cint
from frappe import _

def whitelabel_patch():
	#delete erpnext welcome page 
	frappe.delete_doc_if_exists('Page', 'welcome-to-erpnext', force=1)
	#update Welcome Blog Post
	if frappe.db.exists("Blog Post", "Welcome"):
		frappe.db.set_value("Blog Post","Welcome","content","")
	update_field_label()
	
	# Create or update Whitelabel Setting
	if not frappe.db.exists("Whitelabel Setting", "Whitelabel Setting"):
		doc = frappe.get_doc({
			"doctype": "Whitelabel Setting",
			"name": "Whitelabel Setting",
			"application_logo": "/assets/whitelabel/images/whitelabel_logo.jpg",
			"custom_navbar_title": "ZaynERP",
			"disable_new_update_popup": 1,
			"disable_standard_footer": 1,
			"ignore_onboard_whitelabel": 1
		})
		doc.insert(ignore_permissions=True)
	else:
		doc = frappe.get_doc("Whitelabel Setting", "Whitelabel Setting")
		if not doc.application_logo or not doc.ignore_onboard_whitelabel:
			doc.application_logo = "/assets/whitelabel/images/whitelabel_logo.jpg"
			doc.custom_navbar_title = "ZaynERP"
			doc.disable_new_update_popup = 1
			doc.disable_standard_footer = 1
			doc.ignore_onboard_whitelabel = 1
			doc.save(ignore_permissions=True)
	
	# Add translations
	translations_to_add = [
		{
			"source_text": "ERPNext Settings",
			"translated_text": "ZaynERP Settings",
			"language": "en"
		},
		{
			"source_text": "ERPNext Integrations",
			"translated_text": "ZaynERP Integrations",
			"language": "en"
		}
	]
	
	for translation in translations_to_add:
		# Check if translation exists
		filters = {
			"source_text": translation["source_text"],
			"language": translation["language"]
		}
		
		if not frappe.db.exists("Translation", filters):
			doc = frappe.get_doc({
				"doctype": "Translation",
				"source_text": translation["source_text"],
				"translated_text": translation["translated_text"],
				"language": translation["language"]
			})
			doc.insert(ignore_permissions=True)
		else:
			# Update existing translation
			name = frappe.db.get_value("Translation", filters, "name")
			doc = frappe.get_doc("Translation", name)
			doc.translated_text = translation["translated_text"]
			doc.save(ignore_permissions=True)
	
	if cint(get_frappe_version()) >= 13 and not frappe.db.get_single_value('Whitelabel Setting', 'ignore_onboard_whitelabel'):
		update_onboard_details()


def update_field_label():
	"""Update label of section break in employee doctype"""
	frappe.db.sql("""Update `tabDocField` set label='ERP' where fieldname='erpnext_user' and parent='Employee'""")

def get_frappe_version():
	return frappe.db.get_value("Installed Application",{"app_name":"frappe"},"app_version").split('.')[0]

def update_onboard_details():
	update_onboard_module()
	update_onborad_steps()

def update_onboard_module():
	onboard_module_details = frappe.get_all("Module Onboarding",filters={},fields=["name"])
	for row in onboard_module_details:
		doc = frappe.get_doc("Module Onboarding",row.name)
		doc.documentation_url = ""
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions = True)

def update_onborad_steps():
	onboard_steps_details = frappe.get_all("Onboarding Step",filters={},fields=["name"])
	for row in onboard_steps_details:
		doc = frappe.get_doc("Onboarding Step",row.name)
		doc.intro_video_url = ""
		doc.description = ""
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions = True)

def boot_session(bootinfo):
	"""boot session - send website info if guest"""
	if frappe.session['user']!='Guest':
		bootinfo.whitelabel_setting = frappe.get_doc("Whitelabel Setting","Whitelabel Setting")

@frappe.whitelist()
def ignore_update_popup():
	if not frappe.db.get_single_value('Whitelabel Setting', 'disable_new_update_popup'):
		show_update_popup_update()

@frappe.whitelist()
def show_update_popup_update():
	cache = frappe.cache()
	user  = frappe.session.user
	update_info = cache.get_value("update-info")
	if not update_info:
		return

	updates = json.loads(update_info)

	# Check if user is int the set of users to send update message to
	update_message = ""
	if cache.sismember("update-user-set", user):
		for update_type in updates:
			release_links = ""
			for app in updates[update_type]:
				app = frappe._dict(app)
				release_links += "<b>{title}</b>: <a href='https://github.com/{org_name}/{app_name}/releases/tag/v{available_version}'>v{available_version}</a><br>".format(
					available_version = app.available_version,
					org_name          = app.org_name,
					app_name          = app.app_name,
					title             = app.title
				)
			if release_links:
				message = _("New {} releases for the following apps are available").format(_(update_type))
				update_message += "<div class='new-version-log'>{0}<div class='new-version-links'>{1}</div></div>".format(message, release_links)

	if update_message:
		frappe.msgprint(update_message, title=_("New updates are available"), indicator='green')
		cache.srem("update-user-set", user)