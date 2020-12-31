FORBIDDEN = '_'
READ_ONLY = 'r_o'
WRITE_ONLY = 'w_o'
READ_AND_WRITE = 'r_w'
SHARED = 'shared'
STARRED = 'starred'
PERMISSIONS = (
    (FORBIDDEN, 'FORBIDDEN'),
    (READ_ONLY, 'READ_ONLY'),
    (WRITE_ONLY, 'WRITE_ONLY'),
    (READ_AND_WRITE, 'READ_AND_WRITE')
)
REQUEST_STATUS = (
    ('0', 'NOT_MADE'),
    ('1', 'PENDING'),
    ('2', 'ACCEPT'),
    ('3', 'REJECT')
)
ACCEPT = 'accept'
REJECT = 'reject'
BATCH_SIZE = 20,
REQUEST_STATUS_MAP = {
    'not_made': '0',
    'pending': '1',
    'accept': '2',
    'reject': '3',
}
DEFAULT_ROOT_FOLDER_NAME_TEMPLATE = 'person.user.username'