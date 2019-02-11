import sys
from omeroweb.settings import process_custom_settings, report_settings


def str_not_empty(o):
    s = str(o)
    if not o or not s:
        raise ValueError('Invalid empty value')
    return s


# load settings
SIGNUP_SETTINGS_MAPPING = {
    'omero.web.signup.host':
        ['SIGNUP_HOST', '', str_not_empty, None],
    'omero.web.signup.port':
        ['SIGNUP_PORT', 4064, int, None],
    'omero.web.signup.admin.user':
        ['SIGNUP_ADMIN_USERNAME', '', str_not_empty, None],
    'omero.web.signup.admin.password':
        ['SIGNUP_ADMIN_PASSWORD', '', str_not_empty, None],
    'omero.web.signup.group.name':
        ['SIGNUP_GROUP_NAME', '', str_not_empty, None],
    'omero.web.signup.group.templatetime':
        ['SIGNUP_GROUP_NAME_TEMPLATETIME', False, bool, None],
    'omero.web.signup.group.perms':
        ['SIGNUP_GROUP_PERMS', 'rw----', str_not_empty, None],
    'omero.web.signup.email.enabled':
        ['SIGNUP_EMAIL_ENABLED', False, bool, None],
    'omero.web.signup.email.subject':
        ['SIGNUP_EMAIL_SUBJECT', 'Your OMERO server login details',
         str_not_empty, None],
    'omero.web.signup.email.body':
        ['SIGNUP_EMAIL_BODY', (
            """
            Your login details for OMERO server are:

            username: {username}
            password: {password}
            """
        ), str_not_empty, None],
}


process_custom_settings(sys.modules[__name__], 'SIGNUP_SETTINGS_MAPPING')
report_settings(sys.modules[__name__])
