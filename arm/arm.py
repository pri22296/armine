from itertools import chain
from operator import itemgetter
from collections import namedtuple
from beautifultable import BeautifulTable
from .utils import get_subsets

Rule = namedtuple('Rule', ('antecedent', 'consequent',
                           'confidence', 'lift',
                           'conviction', 'support'))

class ARM(object):
    def __init__(self):
        self._dataset = []
        self._rules = []
        self._itemcounts = {}

    def load_from_csv(self, filename):
        self._dataset = []
        import csv
        with open(filename) as csvfile:
            mycsv = csv.reader(csvfile)
            for row in mycsv:
                self._dataset.append(row)

    def _get_itemcount(self, items):
        try:
            return self._itemcounts[tuple(set(items))]
        except KeyError:
            pass
        count = 0
        for data in self._dataset:
            found = True
            for item in items:
                if item not in data:
                    found = False
                    break
            if found:
                count += 1
        return count

    def load_from_dict(self, data):
        pass

    def _get_initial_itemset(self):
        itemset = []
        items = set(chain(*self._dataset))
        for item in items:
            itemset.append([item])
        return sorted(itemset)

    def _should_join_candidate(self, candidate1, candidate2):
        for i in range(len(candidate1) - 1):
            if candidate1[i] != candidate2[i]:
                return False
        if candidate1[-1] != candidate2[-1]:
            return True
        return False

    def _get_nextgen_itemset(self, itemset):
        new_items = []
        for i in range(len(itemset)):
            for j in range(i, len(itemset)):
                if self._should_join_candidate(itemset[i], itemset[j]):
                    new_items.append(sorted(set(itemset[i] + itemset[j])))
        return new_items

    def _prune_itemset(self, itemset, support_threshold):
        to_be_pruned = []
        for items in itemset:
            item_count = self._get_itemcount(items)
            item_support = round(item_count / len(self._dataset), 3)
            if item_support < support_threshold:
                to_be_pruned.append(items)

        for items in to_be_pruned:
            itemset.remove(items)

    def _match_rule_with_data(self, rule, index):
        data = self._dataset[index]
        return set(rule[0]).issubset(set(data)) and set(rule[0]).issubset(set(data))

    def _prune_rules(self, coverage_threshold):
        pruned_rules = []
        data_cover_count = [0] * len(self._dataset)
        for rule in self._rules:
            rule_add = False
            for i, data in enumerate(self._dataset):
                if self._match_rule_with_data(rule, i)\
                        and data_cover_count[i] >= 0:
                    rule_add = True
                    data_cover_count[i] += 1
                    if data_cover_count[i] >= coverage_threshold:
                        data_cover_count[i] = -1

            if rule_add:
                pruned_rules.append(rule)

        self._rules = pruned_rules

    def _print_rules(self):
        table = BeautifulTable()
        table.column_headers = ['Antecedent', 'Consequent',
                                'Confidence', 'Lift',
                                'Conviction', 'Support']
        table.column_alignments[0] = table.ALIGN_LEFT
        for rule in self._rules:
            table.append_row([', '.join(rule.antecedent),
                              ', '.join(rule.consequent), rule.confidence,
                              rule.lift, rule.conviction,
                              rule.support])

        print(table)

    def _print_items(self):
        for item, count in self._itemcounts.items():
            print(item, count)

    def _get_stats(self, count_a, count_c, count):
        dataset_size = len(self._dataset)
        item_support = round(count_a/dataset_size, 3)
        rule_support = round(count/dataset_size, 3)
        confidence_expected = count_c/dataset_size
        confidence = 0
        lift = 1
        conviction = 1

        try:
            confidence = round(count/count_a, 3)
        except ZeroDivisionError:
            pass

        try:
            lift = round(confidence/confidence_expected, 3)
        except ZeroDivisionError:
            pass

        try:
            conviction = round((1 - (confidence / lift))
                               / (1 - confidence), 3)
        except ZeroDivisionError:
            pass

        return (item_support, rule_support, confidence,
                confidence_expected, lift, conviction)

    def _get_rule(self, antecedent, consequent, support_threshold, confidence_threshold):
        count_a = self._get_itemcount(antecedent)
        count_c = self._get_itemcount(consequent)
        count = self._get_itemcount(tuple(set(antecedent).union(consequent)))

        (item_support, rule_support, confidence,
         confidence_expected, lift, conviction) = self._get_stats(count_a,
                                                                  count_c,
                                                                  count)

        if (confidence >= confidence_threshold) and\
               (item_support >= support_threshold):
            rule = Rule(antecedent, consequent, confidence,
                        lift, conviction, item_support)
        else:
            rule = None

        return rule
            
        

    def _generate_rules(self, itemset, support_threshold, confidence_threshold):
        self._rules = []
        for items in itemset:
            subsets = get_subsets(items)
            for element in subsets:
                remain = set(items).difference(set(element))
                if len(remain) > 0:
                    rule = self._get_rule(tuple(element), tuple(remain), support_threshold, confidence_threshold)
                    if rule is not None:
                        self._rules.append(rule)
        

    def learn(self, support_threshold, confidence_threshold,
              coverage_threshold, *args, **kwargs):
        itemset = self._get_initial_itemset()
        final_itemset = []
        while len(itemset) > 0:
            self._prune_itemset(itemset, support_threshold)
            itemset = self._get_nextgen_itemset(itemset)
            if len(itemset) > 0:
                final_itemset = itemset[:]

        self._generate_rules(final_itemset, support_threshold, confidence_threshold)
        self._prune_rules(coverage_threshold)
        sort_key = lambda rule: (rule.lift, rule.confidence, len(rule.antecedent))
        self._rules.sort(key=sort_key, reverse=True)

