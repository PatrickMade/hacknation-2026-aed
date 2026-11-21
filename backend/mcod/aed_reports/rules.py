import rules

from mcod.lib.rules import assigned_to_organization

rules.add_perm('aed_reports', assigned_to_organization)
rules.add_perm('aed_reports.view_aedincidentreport', assigned_to_organization)
rules.add_perm('aed_reports.change_aedincidentreport', assigned_to_organization)
rules.add_perm('aed_reports.view_aeddevice', assigned_to_organization)
