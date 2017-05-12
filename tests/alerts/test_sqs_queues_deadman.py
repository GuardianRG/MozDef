from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertSQSQueuesDeadman(AlertTestSuite):
    alert_filename = "sqs_queues_deadman"

    default_event = {
        '_source': {
            'utctimestamp': AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 1})
        }
    }

    test_cases = []

    event_dict = {
        '_source': {
            'tags': ['queue1', 'queue2']
        }
    }
    event = AlertTestSuite.create_event(event_dict)
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events containing the specific tags",
            events=[event],
        )
    )

    event_dict = {
        '_source': {
            'tags': ['queue1']
        }
    }
    alert = {
        "category": "deadman",
        "severity": "ERROR",
        "summary": 'No events found from queue2 sqs queue the last hour',
        "tags": ['queue2', 'sqs'],
    }
    event = AlertTestSuite.create_event(event_dict)
    test_cases.append(
        PositiveAlertTestCase(
            description="Postive test case with only an event for one of the tags",
            events=[event],
            expected_alert=alert
        )
    )

    event_dict = {
        '_source': {
            'tags': ['queue2']
        }
    }
    alert = {
        "category": "deadman",
        "severity": "ERROR",
        "summary": 'No events found from queue1 sqs queue the last hour',
        "tags": ['queue1', 'sqs'],
    }
    event = AlertTestSuite.create_event(event_dict)
    test_cases.append(
        PositiveAlertTestCase(
            description="Postive test case with only an event for one of the tags",
            events=[event],
            expected_alert=alert
        )
    )
