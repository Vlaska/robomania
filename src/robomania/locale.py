import logging

logger = logging.getLogger('robomania.locale')


class DefaultLocaleMetaclass(type):
    def __getitem__(cls, name: str) -> str:
        return cls.__dict__[name]


class DefaultLocale(metaclass=DefaultLocaleMetaclass):
    DICE_INCORRECT_EXPRESSION = 'Incorrect expression.'
    DICE_EXPLOSION_DICE_ONLY = 'Cannot explode a group.'
    DICE_REPEAT_ARGUMENT = 'Repeat requires positive argument.'
    DICE_DROP_LOW_ARGUMENT = 'Drop low required positive argument.'
    DICE_KEEP_HIGH_ARGUMENT = 'Keep high required positive argument.'
    DICE_CANNOT_NEGATE_GROUP = 'Cannot negate a group.'
    DICE_INTERNAL_DIV_BY_ZERO = (
        'There was an internal division by 0 (likely caused by dividing by '
        'group). Because of that, division was aborted.'
    )
    DICE_MESSAGE_TOO_LONG = 'Result of the roll was to long to be sent.'
    INTERNAL_ERROR = 'Internal error.'
    DIVISION_BY_ZERO = 'Division by 0.'

    POLL_TOO_MANY_OPTIONS = 'Only 10 options can be passed.'
    POLL_CREATE_MESSAGE_TEMPLATE = '{user} created a poll: "{question}"'

    @classmethod
    def get(cls, name: str) -> str:
        out = cls.__dict__.get(name, None)

        if out is None:
            logger.error(f'Missing default message: "{name}"')
            return name

        return out
