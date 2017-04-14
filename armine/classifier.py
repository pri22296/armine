from operator import itemgetter
from beautifultable import BeautifulTable

from .armine import ARM
from .rule import AssociationRule


class ARMClassifier(ARM):
    def __init__(self):
        super().__init__()
        self._classes = []
        self._default_class = None
        self._is_data_transactional = False

    def load(self, data, is_data_transactional=False):
        self._dataset = []
        self._classes = []
        for features, label in data.items():
            if not is_data_transactional:
                features = ["feature{}-{}".format(i+1, feature)
                            for i, feature in enumerate(features)]
            self._dataset.append(tuple(features))
            self._classes.append((label,))

        self._is_data_transactional = is_data_transactional

    def load_from_csv(self, filename, label_index=0,
                      is_data_transactional=False):
        self._dataset = []
        self._classes = []
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
                if not is_data_transactional:
                    features = ["feature{}-{}".format(i+1, feature)
                                for i, feature in enumerate(features)]
                self._dataset.append(tuple(features))
                self._classes.append((label,))

        self._is_data_transactional = is_data_transactional

    def _get_itemcount(self, items):
        try:
            classwise_count = self._itemcounts[tuple(set(items))]
        except KeyError:
            classwise_count = self._get_classwise_count(items)
        return self._get_itemcount_from_classwise_count(classwise_count)

    def _should_join_candidate(self, candidate1, candidate2):
        if not self._is_data_transactional:
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
            count_class[key[0]] = [0, 0]
        for i, data in enumerate(self._dataset):
            found = True
            for item in items:
                if item not in data:
                    found = False
                    break
            if found:
                count_class[self._classes[i][0]][0] += 1
            count_class[self._classes[i][0]][1] += 1
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
                for label in set(self._classes):
                    classwise_count = self._get_classwise_count(tuple(items))
                    count_a = self._get_itemcount_from_classwise_count(classwise_count)
                    count_c = classwise_count[label[0]][1]
                    count_b = classwise_count[label[0]][0]
                    rule = AssociationRule(tuple(items), label,
                                       count_b, count_a, count_c,
                                       len(self._dataset))
                    cba2_sup_th = support_threshold * (count_c / len(self._dataset))
                    if (rule.confidence >= confidence_threshold and
                            rule.support >= cba2_sup_th):
                        self._rules.append(rule)

    def print_rules(self):
        table = BeautifulTable()
        table.column_headers = ['Antecedent', 'Consequent',
                                'Confidence', 'Lift',
                                'Conviction', 'Support']
        table.column_alignments[0] = table.ALIGN_LEFT
        table.column_alignments[1] = table.ALIGN_LEFT
        for rule in self._rules:
            antecedent = [item.split('-')[1]
                          if not self._is_data_transactional
                          else item for item in rule.antecedent]
            table.append_row([', '.join(antecedent),
                              ', '.join(rule.consequent),
                              rule.confidence,
                              rule.lift,
                              rule.conviction,
                              rule.support])

        print(table)

    def _get_default_class(self, support_threshold, confidence_threshold):
        counter = dict.fromkeys(set(self._classes), 0)
        for i, _ in enumerate(self._dataset):
            is_match = False
            for rule in self._rules:
                if rule.support < support_threshold\
                       or rule.confidence < confidence_threshold:
                    continue
                if (rule.match_antecedent(self._dataset[i]) and
                        rule.match_consequent(self._classes[i])):
                    is_match = True
                    break
            if is_match is False:
                counter[self._classes[i]] += 1

        return max(counter.items(), key=itemgetter(1))[0]

    def learn(self, support_threshold, confidence_threshold,
              coverage_threshold=20):
        super().learn(support_threshold, confidence_threshold,
                      coverage_threshold)
        self._default_class = self._get_default_class(
                           support_threshold,
                           confidence_threshold)

    def classify(self, data, support_threshold, confidence_threshold,
                 top_k_rules=25):
        matching_rules = []
        for rule in self._rules:
            if rule.support < support_threshold\
                   or rule.confidence < confidence_threshold:
                continue
            if rule.match_antecedent(data):
                matching_rules.append(rule)
            if len(matching_rules) == top_k_rules:
                break
        if len(matching_rules) > 0:
            score = dict()
            for rule in matching_rules:
                label = rule.consequent[0]
                score[label] = (score.get(label, 0)
                                          + rule.lift)
            return max(score.items(), key=itemgetter(1))[0]
        else:
            return self._default_class
