from arm import ARM, ARMClassifier

def test_arm():
    ar = ARM()
    ar.load_from_csv('data.csv')
    ar.learn(0.3, 0.1, 10)
    ar._print_rules()

def test_arm_classifier():
    ar = ARMClassifier()
    ar.load_from_csv('raw.csv', -1, False)
    ar.learn(0.3, 0.1, 10)
    ar._print_rules()

def main():
    test_arm()
    test_arm_classifier()

if __name__ == '__main__':
    main()
