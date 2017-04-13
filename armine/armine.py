from itertools import chain
from collections import namedtuple
from beautifultable import BeautifulTable

from .utils import get_subsets
from .rule import AssociationRule


def _get_rule_key(rule):
    return (rule.lift, rule.confidence, len(rule.antecedent))


class ARM(object):
    def __init__(self):
        self._dataset = []
        self._rules = []
        self._itemcounts = {}

    @property
    def rules(self):
        return self._rules

    def load(self, data):
        self._dataset = []
        for row in data:
            self._dataset.append(list(row))

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
        for i, _ in enumerate(itemset):
            for j in range(i, len(itemset)):
                if self._should_join_candidate(itemset[i], itemset[j]):
                    new_items.append(sorted(set(itemset[i]).union(itemset[j])))
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
        return set(rule[0]).issubset(set(data))\
            and set(rule[0]).issubset(set(data))

    def _prune_rules(self, coverage_threshold):
        pruned_rules = []
        data_cover_count = [0] * len(self._dataset)
        for rule in self._rules:
            rule_add = False
            for i, data in enumerate(self._dataset):
                if (rule.match_antecedent(data)
                        and data_cover_count[i] >= 0):
                    rule_add = True
                    data_cover_count[i] += 1
                    if data_cover_count[i] >= coverage_threshold:
                        data_cover_count[i] = -1

            if rule_add:
                pruned_rules.append(rule)

        self._rules = pruned_rules

    def print_rules(self):
        table = BeautifulTable()
        table.column_headers = ['Antecedent', 'Consequent',
                                'Confidence', 'Lift',
                                'Conviction', 'Support']
        table.column_alignments[0] = table.ALIGN_LEFT
        for rule in self._rules:
            table.append_row([', '.join(rule.antecedent),
                              ', '.join(rule.consequent), round(rule.confidence, 3),
                              round(rule.lift, 3), round(rule.conviction, 3),
                              round(rule.support, 3)])

        print(table)

    def _print_items(self):
        for item, count in self._itemcounts.items():
            print(item, count)

    def _generate_rules(self, itemset, support_threshold,
                        confidence_threshold):
        for items in itemset:
            subsets = get_subsets(items)
            for element in subsets:
                remain = set(items).difference(set(element))
                if len(remain) > 0:
                    count_a = self._get_itemcount(element)
                    count_c = self._get_itemcount(remain)
                    count_b = self._get_itemcount(items)
                    rule = AssociationRule(tuple(element), tuple(remain),
                                           count_b, count_a, count_c,
                                           len(self._dataset))
                    if (rule.confidence >= confidence_threshold and
                            rule.support >= support_threshold):
                        self._rules.append(rule)

    def learn(self, support_threshold, confidence_threshold,
              coverage_threshold=20):
        itemset = self._get_initial_itemset()
        self._rules = []
        while len(itemset) > 0:
            self._prune_itemset(itemset, support_threshold)
            self._generate_rules(itemset, support_threshold,
                                 confidence_threshold)
            itemset = self._get_nextgen_itemset(itemset)

        self._rules = list(set(self._rules))
        self._prune_rules(coverage_threshold)
        self._rules.sort(key=_get_rule_key, reverse=True)
