from app.utils.transliterate import transliterate, safe_filename_with_cyrillic


class TestTransliterate:

    def test_latin_passthrough(self):
        assert transliterate("hello") == "hello"

    def test_digits_passthrough(self):
        assert transliterate("123") == "123"

    def test_special_chars_passthrough(self):
        assert transliterate("a-b_c.d") == "a-b_c.d"

    def test_lowercase_cyrillic(self):
        assert transliterate("привет") == "privet"

    def test_uppercase_cyrillic(self):
        assert transliterate("Привет") == "Privet"

    def test_all_lowercase_letters(self):
        result = transliterate("абвгдежзийклмнопрстуфхцчшщъыьэюя")
        assert result == "abvgdezhziyklmnoprstufhtschshschyeyuya"

    def test_all_uppercase_letters(self):
        result = transliterate("АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ")
        assert result == "ABVGDEZhZIYKLMNOPRSTUFHTsChShSchYEYuYa"

    def test_mixed_cyrillic_latin(self):
        assert transliterate("Файл123") == "Fayl123"

    def test_empty_string(self):
        assert transliterate("") == ""

    def test_hard_sign_removed(self):
        assert transliterate("ъ") == ""

    def test_soft_sign_removed(self):
        assert transliterate("ь") == ""

    def test_yo(self):
        assert transliterate("ё") == "yo"

    def test_yo_uppercase(self):
        assert transliterate("Ё") == "Yo"

    def test_full_name(self):
        assert transliterate("Иванов Иван") == "Ivanov Ivan"


class TestSafeFilenameWithCyrillic:

    def test_latin_filename(self):
        result = safe_filename_with_cyrillic("report.pdf")
        assert result == "report.pdf"

    def test_cyrillic_filename(self):
        result = safe_filename_with_cyrillic("отчет.pdf")
        assert result == "otchet.pdf"

    def test_cyrillic_with_spaces(self):
        result = safe_filename_with_cyrillic("мой файл.doc")
        # secure_filename replaces spaces with underscores or strips them
        assert result.endswith(".doc")
        assert "moy" in result

    def test_mixed_cyrillic_latin(self):
        result = safe_filename_with_cyrillic("Доклад2024.pdf")
        assert result == "Doklad2024.pdf"

    def test_dots_in_name(self):
        result = safe_filename_with_cyrillic("файл.версия2.txt")
        # rsplit('.', 1) splits only on last dot
        assert result.endswith(".txt")

    def test_path_traversal_stripped(self):
        result = safe_filename_with_cyrillic("../../../отчет.pdf")
        # secure_filename should strip path components
        assert ".." not in result
        assert result.endswith(".pdf")
