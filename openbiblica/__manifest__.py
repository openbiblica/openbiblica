{
    'name' : 'Openbiblica',
    'version' : '1.0',
    'summary': 'OpenBiblica Models',
    'sequence': 1,
    'description': """
    OpenBiblica is a web based bible translation platform
    This module contents the basic models and backend views
    """,
    'author': "Kusuma Ruslan",
    'website': "http://www.openbiblica.com",
    'category': 'Website',
    'depends': ['website_forum'],
    'data': [
        'security/ir.model.access.csv',
        'views/biblica.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

