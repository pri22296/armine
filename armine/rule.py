from math import sqrt
from functools import wraps


def on_zero_error(default_value):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except ZeroDivisionError:
                result = default_value
            return result
        return wrapper
    return decorator


class AssociationRule(object):
    def __init__(self, antecedent, consequent, count_both,
                 count_lhs, count_rhs, datasize):
        self._count_lhs = count_lhs
        self._count_both = count_both
        self._count_rhs = count_rhs
        self._datasize = datasize
        self._antecedent = antecedent
        self._consequent = consequent

    def __eq__(self, other):
        return (self._antecedent == other._antecedent
                and self._consequent == other._consequent
                and self._count_lhs == other._count_lhs
                and self._count_both == other._count_both
                and self._count_rhs == other._count_rhs
                and self._datasize == other._datasize)

    def __hash__(self):
        return (hash(self._antecedent)
                + hash(self._consequent)
                + hash(self._count_lhs)
                + hash(self._count_both)
                + hash(self._count_rhs)
                + hash(self._datasize))

    def __str__(self):
        lhs = ', '.join(self._antecedent)
        rhs = ', '.join(self._consequent)
        return "{} ==> {}".format(lhs, rhs)

    # ********************* Properties begin here *************************** #
    @property
    def antecedent(self):
        return self._antecedent

    @property
    def consequent(self):
        return self._consequent

    @property
    def support(self):
        return self._count_both / self._datasize

    @property
    def coverage(self):
        return self._count_lhs / self._datasize

    @property
    def strength(self):
        return self._count_rhs / self._count_lhs

    @property
    @on_zero_error(0)
    def confidence(self):
        return self._count_both / self._count_lhs

    @property
    def confidence_expected(self):
        return self._count_rhs / self._datasize

    @property
    @on_zero_error(1)
    def lift(self):
        return ((self._datasize * self._count_both)
                / (self._count_lhs * self._count_rhs))

    @property
    def leverage(self):
        return ((self._datasize * self._count_both)
                - (self._count_lhs * self._count_rhs))

    @property
    @on_zero_error(1)
    def conviction(self):
        return (1 - (self._count_rhs / self._datasize)) / (1 - self.confidence)

    @property
    def cosine(self):
        return self._count_both / sqrt(self._count_lhs * self._count_rhs)

    @property
    def added_value(self):
        return self._datasize * self.confidence / self._count_rhs

    # ******************** Properties end here ****************************** #

    def match_antecedent(self, items):
        return set(self._antecedent).issubset(items)

    def antecedent2str(self):
        return ', '.join(self._antecedent)

    def match_consequent(self, items):
        return set(self._consequent).issubset(items)

    def consequent2str(self):
        return ', '.join(self._consequent)


class ClassificationRule(AssociationRule):

    def __str__(self):
        lhs = ', '.join(self._antecedent)
        rhs = self._consequent
        return "{} ==> {}".format(lhs, rhs)

    def match_consequent(self, label):
        return self._consequent == label

    def consequent2str(self):
        return self._consequent
