from .arm import ARM, Rule
from .utils import get_subsets
from operator import itemgetter
from beautifultable import BeautifulTable

class ARMClassifier(ARM):
    def __init__(self):
        super().__init__()
        self._default_class = None

    def load_from_csv(self, filename, label_index=0, is_data_transactional=False):
        self._dataset = []
        self._classes = []
        import csv
        with open(filename) as csvfile:
            mycsv = csv.reader(csvfile)
            for i, row in enumerate(mycsv):
                label = row[label_index]
                if label_index >= 0:
                    features = row[:label_index] + row[label_index + 1:]
                else:
                    features = row[:len(row) + label_index] + row[len(row) + label_index + 1:]
                if not is_data_transactional:
                    features = ["feature{}-{}".format(i+1, feature) for i, feature in enumerate(features)]
                self._dataset.append(features)
                self._classes.append(label)

        self._is_data_transactional = is_data_transactional

    def _get_itemcount(self, items):
        try:
            classwise_count = self._itemcounts[tuple(set(items))]
        except KeyError:
            classwise_count = self._get_classwise_count(items)
        return self._get_itemcount_from_classwise_count(classwise_count)

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

    def _get_itemcount_from_classwise_count(self, classwise_count):
        net_itemcount = 0
        for itemcount, _ in classwise_count.values():
            net_itemcount += itemcount
        return net_itemcount

    def _get_rule(self, antecedent, consequent, support_threshold, confidence_threshold):
        classwise_count = self._get_classwise_count(antecedent)
        item_count = self._get_itemcount_from_classwise_count(classwise_count)

        count_a = item_count
        count_c = classwise_count[consequent][1]
        count = classwise_count[consequent][0]

        (item_support, rule_support, confidence,
         confidence_expected, lift, conviction) = self._get_stats(count_a,
                                                                  count_c,
                                                                  count)

        if (confidence >= confidence_threshold) and\
               (rule_support >= support_threshold * confidence_expected):
            rule = Rule(antecedent, consequent, confidence,
                        lift, conviction, item_support)
        else:
            rule = None

        return rule

    def _generate_rules(self, itemset, support_threshold, confidence_threshold):
        dataset_length = len(self._dataset)
        for elements in itemset:
            subsets = get_subsets(elements)
            for items in subsets:
                if len(items) > 0:
                    for label in set(self._classes):
                        rule = self._get_rule(tuple(items), label, support_threshold, confidence_threshold)
                        if rule is not None:
                            self._rules.append(rule)

        self._rules = list(set(self._rules))

    def _print_rules(self):
        table = BeautifulTable()
        table.column_headers = ['Antecedent', 'Consequent',
                                'Confidence', 'Lift',
                                'Conviction', 'Support']
        table.column_alignments[0] = table.ALIGN_LEFT
        for rule in self._rules:
            antecedent = [item.split('-')[1] if not self._is_data_transactional else item for item in rule.antecedent]
            table.append_row([', '.join(antecedent),
                              rule.consequent, rule.confidence,
                              rule.lift, rule.conviction,
                              rule.support])

        print(table)

    def _match_rule_with_data(self, rule, index):
        if not isinstance(index, int):
            data = index
            label = None
        else:
            data = self._dataset[index]
            label = self._classes[index]
        return (set(rule.antecedent).issubset(data) and
                    ((rule.consequent == label) or (label is None)))

    def learn(self, support_threshold, confidence_threshold, coverage_threshold):
        super().learn(support_threshold, confidence_threshold, coverage_threshold)
        self._default_class = self._get_default_class(support_threshold,
                                                      confidence_threshold)

    def _get_default_class(self, support_threshold, confidence_threshold):
        counter = dict.fromkeys(set(self._classes), 0)
        for i, data in enumerate(self._dataset):
            is_match = False
            for rule in self._rules:
                if rule.support < support_threshold\
                       or rule.confidence < confidence_threshold:
                    continue
                if self._match_rule_with_data(rule, i):
                    is_match = True
                    break
            if is_match is False:
                counter[self._classes[i]] += 1

        return max(counter.items(), key=itemgetter(1))[0]

    def classify(self, data, support_threshold, confidence_threshold, top_k_rules):
        matching_rules = []
        for rule in self._rules:
            if rule.support < support_threshold\
                   or rule.confidence < confidence_threshold:
                continue
            if self._match_rule_with_data(rule, data):
                matching_rules.append(rule)
            if len(matching_rules) == top_k_rules:
                break
        if len(matching_rules) > 0:
            score = dict()
            for rule in matching_rules:
                score[rule.consequent] = (score.get(rule.consequent, 0)
                                          + rule.lift)
            return max(score.items(), key=itemgetter(1))[0]
        else:
            return self._default_class
