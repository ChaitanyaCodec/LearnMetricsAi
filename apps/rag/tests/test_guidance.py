from django.test import SimpleTestCase

from apps.rag.guidance import QueryGuidanceService


class QueryGuidanceServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = QueryGuidanceService()

    def test_no_context_guidance_without_subject(self):
        result = self.service.build(
            question="Tell me something",
        )

        self.assertEqual(
            result.reason,
            QueryGuidanceService.NO_RELEVANT_CONTEXT,
        )

        self.assertIn(
            "uploaded study material",
            result.message,
        )

        self.assertGreaterEqual(
            len(result.suggestions),
            3,
        )

    def test_no_context_guidance_with_subject(self):
        result = self.service.build(
            question="Tell me something",
            subject="Big Data Analytics",
        )

        self.assertEqual(
            result.reason,
            QueryGuidanceService.NO_RELEVANT_CONTEXT,
        )

        self.assertIn(
            "Big Data Analytics",
            result.message,
        )

        self.assertIn(
            "Big Data Analytics",
            result.suggestions[0],
        )

    def test_clarification_guidance_with_subject(self):
        result = self.service.build(
            question="Explain this",
            reason=QueryGuidanceService.CLARIFICATION,
            subject="Big Data Analytics",
        )

        self.assertEqual(
            result.reason,
            QueryGuidanceService.CLARIFICATION,
        )

        self.assertIn(
            "specific",
            result.message.lower(),
        )

        self.assertGreaterEqual(
            len(result.suggestions),
            3,
        )

    def test_suggestions_are_deduplicated(self):
        suggestions = (
            "Question A",
            "Question A",
            " question a ",
            "",
            "Question B",
        )

        result = self.service._deduplicate_suggestions(
            suggestions
        )

        self.assertEqual(
            result,
            (
                "Question A",
                "Question B",
            ),
        )

    def test_guidance_output_is_deterministic(self):
        first = self.service.build(
            question="Tell me something",
            subject="Big Data Analytics",
        )

        second = self.service.build(
            question="Tell me something",
            subject="Big Data Analytics",
        )

        self.assertEqual(first, second)