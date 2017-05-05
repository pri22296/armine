from armine import ARM, ARMClassifier
import unittest

ARM_TEST_FILENAME = 'sample//arm_sample.csv'
ARM_TEST_DATA = [['Bread', 'Milk'],
                 ['Bread', 'Diapers', 'Beer', 'Eggs'],
                 ['Milk', 'Diapers', 'Beer', 'Cola'],
                 ['Bread', 'Milk', 'Diapers', 'Beer'],
                 ['Bread', 'Milk', 'Diapers', 'Cola']]

ARM_CLASSIFIER_TEST_FILENAME = 'sample//classifier_sample.csv'
ARM_CLASSIFIER_TEST_DATA = {('Egg','Chicken'): 'NV',
                            ('Milk','Egg','Spinach'): 'M',
                            ('Chicken','Milk'): 'M',
                            ('Milk','Spinach'): 'V',}

class ARMTestCase(unittest.TestCase):
    def setUp(self):
        self.arm = ARM()

    def compare_iterable(self, iterable1, iterable2):
        for item1, item2 in zip(iterable1, iterable2):
            self.assertEqual(item1, item2)

    def compare_data(self, data):
        for row, row1 in zip(data, self.arm._dataset):
            self.compare_iterable(row, row1)

    def learn(self, support_threshold, confidence_threshold,
              coverage_threshold):
        self.arm.load(ARM_TEST_DATA)
        self.arm.learn(support_threshold, confidence_threshold,
                       coverage_threshold)

    def check_real(self, support_threshold, confidence_threshold,
              coverage_threshold):
        self.assertEqual(self.arm._real_support_threshold,
                         support_threshold)
        self.assertEqual(self.arm._real_confidence_threshold,
                         confidence_threshold)
        self.assertEqual(self.arm._real_coverage_threshold,
                         coverage_threshold)

    def check_apparent(self, support_threshold, confidence_threshold,
              coverage_threshold):
        self.assertEqual(self.arm._apparent_support_threshold,
                         support_threshold)
        self.assertEqual(self.arm._apparent_confidence_threshold,
                         confidence_threshold)
        self.assertEqual(self.arm._apparent_coverage_threshold,
                         coverage_threshold)

    def check(self, support_threshold, confidence_threshold,
              coverage_threshold):
        self.check_real(support_threshold, confidence_threshold,
              coverage_threshold)
        self.check_apparent(support_threshold, confidence_threshold,
              coverage_threshold)
        self.assertEqual(len(self.arm.rules), len(self.arm._rules))

    def test_load_data(self):
        self.arm.load(ARM_TEST_DATA)
        self.compare_data(ARM_TEST_DATA)

    def test_load_data_from_csv(self):
        self.arm.load_from_csv(ARM_TEST_FILENAME)
        self.compare_data(ARM_TEST_DATA)

    def test_learn(self):
        self.learn(0.2, 0.1, 20)
        self.check(0.2, 0.1, 20)

    def test_learn_support_increase(self):
        self.learn(0.2, 0.1, 20)
        self.learn(0.3, 0.1, 20)
        
        self.check_real(0.2, 0.1, 20)
        self.check_apparent(0.3, 0.1, 20)
        self.assertTrue(len(self.arm.rules) <= len(self.arm._rules))

    def test_learn_confidence_increase(self):
        self.learn(0.2, 0.1, 20)
        self.learn(0.2, 0.2, 20)
        
        self.check_real(0.2, 0.1, 20)
        self.check_apparent(0.2, 0.2, 20)
        self.assertTrue(len(self.arm.rules) <= len(self.arm._rules))

    def test_learn_coverage_modify(self):
        self.learn(0.2, 0.1, 20)
        self.learn(0.3, 0.2, 25)
        self.check(0.3, 0.2, 25)

    def test_learn_support_increase_confidence_decrease(self):
        self.learn(0.2, 0.1, 20)
        self.learn(0.3, 0.05, 20)
        self.check(0.3, 0.05, 20)

    def test_learn_support_decrease_confidence_increase(self):
        self.learn(0.2, 0.1, 20)
        self.learn(0.1, 0.2, 20)
        self.check(0.1, 0.2, 20)

    def test_rules(self):
        self.learn(0.2, 0.1, 20)
        rules1 = self.arm.rules[:]
        self.learn(0.3, 0.2, 20)
        rules2 = self.arm.rules[:]
        for rule in rules1:
            self.assertTrue(rule.coverage >= 0.2 and rule.confidence >= 0.1)
        for rule in rules2:
            self.assertTrue(rule.coverage >= 0.3 and rule.confidence >= 0.2)

    def test_initial_itemset(self):
        expected = ['Beer', 'Bread', 'Cola', 'Diapers', 'Milk']
        itemset = self.arm._get_initial_itemset()
        self.compare_iterable(itemset, expected)

    def test_itemcount(self):
        self.arm.load(ARM_TEST_DATA)
        count = self.arm._get_itemcount(['Beer'])
        self.assertEqual(count, 3)

        count = self.arm._get_itemcount(['Beer', 'Bread'])
        self.assertEqual(count, 2)

        count = self.arm._get_itemcount(['Beer', 'Bread', 'Cola'])
        self.assertEqual(count, 0)

class ARMClassifierTestCase(unittest.TestCase):
    def setUp(self):
        self.arm = ARMClassifier()

    def compare_iterable(self, iterable1, iterable2):
        for item1, item2 in zip(iterable1, iterable2):
            self.assertEqual(item1, item2)

    def compare_classwise_counts(self, count1, count2):
        self.assertEqual(len(count1), len(count2))
        for label in count1:
            self.compare_iterable(count1[label], count2[label])

    def compare_data(self, data):
        items = sorted(list(data.items()))
        items1 = sorted(list(zip(self.arm._dataset, self.arm._classes)))
        for item, item1 in zip(items, items1):
            self.compare_iterable(item[0], item1[0])
            self.assertEqual(item[1], item1[1])

    def test_load_data(self):
        self.arm.load(ARM_CLASSIFIER_TEST_DATA, True)
        self.compare_data(ARM_CLASSIFIER_TEST_DATA)

    def test_load_data_from_csv(self):
        self.arm.load_from_csv(ARM_CLASSIFIER_TEST_FILENAME, -1, True)
        self.compare_data(ARM_CLASSIFIER_TEST_DATA)

    def test_classwise_count(self):
        self.arm.load(ARM_CLASSIFIER_TEST_DATA, True)
        count = self.arm._get_classwise_count(['Milk'])
        self.compare_classwise_counts(count, {'V': [1, 1],
                                              'NV': [0, 1],
                                              'M': [2, 2]})

        count = self.arm._get_classwise_count(['Milk', 'Spinach'])
        self.compare_classwise_counts(count, {'V': [1, 1],
                                              'NV': [0, 1],
                                              'M': [1, 2]})

    def test_itemcount(self):
        self.arm.load(ARM_CLASSIFIER_TEST_DATA, True)
        count = self.arm._get_itemcount(['Milk'])
        self.assertEqual(count, 3)

        count = self.arm._get_itemcount(['Milk', 'Spinach'])
        self.assertEqual(count, 2)

        count = self.arm._get_itemcount(['Milk', 'Spinach', 'Chicken'])
        self.assertEqual(count, 0)

    def learn(self, support_threshold, confidence_threshold,
              coverage_threshold):
        self.arm.load(ARM_CLASSIFIER_TEST_DATA, True)
        self.arm.learn(support_threshold, confidence_threshold,
                       coverage_threshold)

    def test_learn(self):
        self.learn(0.2, 0.1, 20)
        self.assertTrue(self.arm._default_class in self.arm._classes)
        for rule in self.arm._rules:
            self.assertTrue(rule.consequent in self.arm._classes)

def test_arm():
    ar = ARM()
    ar.load(data1)
    ar.learn(0.1, 0.1)
    ar.print_rules()


def test_arm_classifier():
    ar = ARMClassifier()
    ar.load_from_csv('testdata/raw.csv', -1, False)
    ar.learn(0.3, 0.1)
    ar.print_rules()
    ar.learn(0.6, 0.1)
    ar.print_rules()
    ar.learn(0.8, 0.1)
    ar.print_rules()
    data = ['April', 'Div6' ,'Dep4',
            'Normal', 'MH', 'GW', 'MW',
            'UC', 'Employee', 'SPI1',
            'IPS3', 'EDS5', 'SS12',
            'BD2', 'Beh', 'SINF']
    result = ar.classify(data)
    print(result)


def main():
    test_arm()
    test_arm_classifier()


if __name__ == '__main__':
    unittest.main()
