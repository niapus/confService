import pytest

from app.service.markdown_service import MarkdownService


@pytest.fixture
def markdown_service():
    return MarkdownService()


class TestToHtml:

    def test_converts_markdown_to_html(self, markdown_service):
        result = markdown_service.to_html("# Hello")
        assert "<h1>" in result
        assert "Hello" in result

    def test_converts_bold(self, markdown_service):
        result = markdown_service.to_html("**bold**")
        assert "<strong>bold</strong>" in result

    def test_converts_italic(self, markdown_service):
        result = markdown_service.to_html("*italic*")
        assert "<em>italic</em>" in result

    def test_converts_link(self, markdown_service):
        result = markdown_service.to_html("[link](https://example.com)")
        assert 'href="https://example.com"' in result
        assert "link" in result

    def test_converts_unordered_list(self, markdown_service):
        result = markdown_service.to_html("- item1\n- item2")
        assert "<ul>" in result
        assert "<li>" in result

    def test_converts_ordered_list(self, markdown_service):
        result = markdown_service.to_html("1. first\n2. second")
        assert "<ol>" in result
        assert "<li>" in result

    def test_converts_code_block(self, markdown_service):
        result = markdown_service.to_html("```\ncode\n```")
        assert "<code>" in result or "<pre>" in result

    def test_sanitizes_script_tags(self, markdown_service):
        result = markdown_service.to_html("<script>alert('xss')</script>")
        assert "<script>" not in result

    def test_sanitizes_onclick(self, markdown_service):
        result = markdown_service.to_html('<a onclick="alert(1)">click</a>')
        assert "onclick" not in result

    def test_allows_table_tags(self, markdown_service):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        result = markdown_service.to_html(md)
        assert "<table>" in result

    def test_empty_input(self, markdown_service):
        result = markdown_service.to_html("")
        assert result is not None

    def test_converts_paragraph(self, markdown_service):
        result = markdown_service.to_html("Simple text")
        assert "Simple text" in result

    def test_multiple_calls_independent(self, markdown_service):
        result1 = markdown_service.to_html("# First")
        result2 = markdown_service.to_html("# Second")
        assert "First" in result1
        assert "Second" in result2
