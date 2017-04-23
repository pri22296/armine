from operator import itemgetter

from .armine import ARM
from .rule import ClassificationRule


class ARMClassifier(ARM):
    """Utility class for Classification Rule Mining.

    This class provides methods to generate a set of Classification rules
    from a transactional dataset or a tabular dataset. You can then use this
    class to classify unclassified data instances. The classification is done
    using a modified version of the CBA Algorithm.
    """
    def __init__(self):
        super().__init__()
        self._classes = []
        self._default_class = None
        self._transactional_database = False

    def load(self, data, transactional_database=False):
        """Load dataset from a Dictionary.

        Parameters
        ----------
        data : dict
            Dictionary with keys as features and values as labels.

        transactional_database : bool
            Whether the database is transactional(Default False).

        Note
        ----
        A database is transactional, if it contains transactions accompanied
        with respective labels. On the other hand, A non transactional database
        is basically a tabular dataset, with each column representing a distinct
        feature.
        """
        self._clear()
        for features, label in data.items():
            if not transactional_database:
                features = ["feature{}-{}".format(i+1, feature)
                            for i, feature in enumerate(features)]
            self._dataset.append(tuple(features))
            self._classes.append(label)

        self._transactional_database = transactional_database

    def load_from_csv(self, filename, label_index=0,
                      transactional_database=False):
        """Load dataset from a csv file.

        Parameters
        ----------
        filename : string
            Name of the csv file which contains the dataset.

        label_index : int
            Index of the column which contains the labels for each row. Supports
            negative indexing(Default -1 which corresponds to the last column).

        transactional_database : bool
            Whether the database is transactional(Default False).
        """
        self._clear()
        import csv
        with open(filename) as csvfile:
            mycsv = csv.reader(csvfile)
            for row in mycsv:
                label = row[label_index]
                if label_index >= 0:
                    features = row[:label_index] + row[label_index + 1:]
                else:
                    features = (row[:len(row) + label_index]
                                + row[len(row) + label_index + 1:])
                if not transactional_database:
                    features = ["feature{}-{}".format(i+1, feature)
                                for i, feature in enumerate(features)]
                self._dataset.append(tuple(features))
                self._classes.append(label)

        self._transactional_database = transactional_database

    def _clear(self):
        super()._clear()
        self._classes = []

    def _clean_items(self, items):
        if not self._transactional_database:
            return tuple([feature.split('-')[1] for feature in items])
        else:
            return tuple(items)

    def _get_itemcount(self, items):
        try:
            classwise_count = self._itemcounts[tuple(set(items))]
        except KeyError:
            classwise_count = self._get_classwise_count(items)
        return self._get_itemcount_from_classwise_count(classwise_count)

    def _should_join_candidate(self, candidate1, candidate2):
        if not self._transactional_database:
            # If the last entry of both candidates belong to different
            # classes in a non transactional database
            # then they cannot be joined as the resulting
            # candidate would have support 0.
            feature1 = candidate1[-1].split('-')[0]
            feature2 = candidate2[-1].split('-')[0]
            if (feature1 == feature2):
                return False
        return super()._should_join_candidate(candidate1, candidate2)

    def _get_classwise_count(self, items):
        count_class = dict()
        for key in set(self._classes):
            count_class[key] = [0, 0]
        for i, data in enumerate(self._dataset):
            found = True
            for item in items:
                if item not in data:
                    found = False
                    break
            if found:
                count_class[self._classes[i]][0] += 1
            count_class[self._classes[i]][1] += 1
        return count_class

    @staticmethod
    def _get_itemcount_from_classwise_count(classwise_count):
        net_itemcount = 0
        for itemcount, _ in classwise_count.values():
            net_itemcount += itemcount
        return net_itemcount

    def _generate_rules(self, itemset, support_threshold,
                        confidence_threshold):
        for items in itemset:
            if len(items) > 0:
                rules = []
                for label in set(self._classes):
                    classwise_count = self._get_classwise_count(tuple(items))
                    count_a = self._get_itemcount_from_classwise_count(classwise_count)
                    count_c = classwise_count[label][1]
                    count_b = classwise_count[label][0]
                    antecedent = self._clean_items(items)
                    rule = ClassificationRule(antecedent, label,
                                       count_b, count_a, count_c,
                                       len(self._dataset))
                    if (rule.confidence >= confidence_threshold and
                            rule.coverage >= support_threshold):
                        rules.append(rule)
                rules.sort(key=self._rule_key)
                try:
                    self._rules.append(rules[-1])
                except IndexError:
                    pass

    def _get_default_class(self, support_threshold, confidence_threshold):
        counter = dict.fromkeys(set(self._classes), 0)
        for i, _ in enumerate(self._dataset):
            is_match = False
            for rule in self._rules:
                if rule.coverage < support_threshold\
                       or rule.confidence < confidence_threshold:
                    continue
                items = self._clean_items(self._dataset[i])
                if (rule.match_antecedent(items) and
                        rule.match_consequent(self._classes[i])):
                    is_match = True
                    break
            if is_match is False:
                counter[self._classes[i]] += 1
        return max(counter.items(), key=itemgetter(1))[0]

    def learn(self, support_threshold, confidence_threshold,
              coverage_threshold=20):
        """Generate Classification rules from the Training dataset.

        Parameters
        ----------
        support_threshold : float
            User defined threshold between 0 and 1. Rules with support
            less than `support_threshold` are not generated.

        confidence_threshold : float
            User defined threshold between 0 and 1. Rules with confidence
            less than `confidence_threshold` are not generated.

        coverage_threshold : int
            Maximum number of rules, a specific transaction can match.
            After it exceeds this, That row is no longer considered for
            matching other rules. Using this process all rules are removed,
            which do not match any transaction left(Default 20).
        """
        super().learn(support_threshold, confidence_threshold,
                      coverage_threshold)
        self._default_class = self._get_default_class(
                           support_threshold,
                           confidence_threshold)

    def classify(self, data_instance, support_threshold, confidence_threshold,
                 top_k_rules=25):
        """Classify `data_instance` using rules generated by `learn` method.

        Parameters
        ----------
        data_instance : array_like
            Unclassified input.

        support_threshold : float
            User defined threshold between 0 and 1. Rules with support
            less than `support_threshold` are ignored.

        confidence_threshold : float
            User defined threshold between 0 and 1. Rules with confidence
            less than `confidence_threshold` are ignored.

        top_k_rules : int
            Maximum number of rules, which will be used to classify
            `data_instance`.

        Returns
        -------
        str
            Predicted label for the `data_instance`.

        Note
        ----
        If the support_threshold and confidence_threshold passed to classify
        are both greater than the values at which learning was done,
        The result is same as if the learning is done at those higher values.
        This helps in optimization purposes where you only need to learn once
        at a low support and confidence_threshold, which reduces optimization
        time.
        """
        matching_rules = []
        for rule in self._rules:
            if (rule.coverage < support_threshold or
                  rule.confidence < confidence_threshold):
                continue
            if rule.match_antecedent(data_instance):
                matching_rules.append(rule)
            if len(matching_rules) == top_k_rules:
                break
        if len(matching_rules) > 0:
            score = dict()
            for rule in matching_rules:
                label = rule.consequent
                score[label] = (score.get(label, 0) + rule.lift)
            return max(score.items(), key=itemgetter(1))[0]
        else:
            return self._default_class
