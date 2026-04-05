import os
import tempfile
import unittest
from pathlib import Path

from computer_use.skills import (
    Skill,
    discover_skills,
    load_skill,
    parse_frontmatter,
    skills_to_tools,
)


class TestSkills(unittest.TestCase):
    # 1
    def test_parse_frontmatter_extracts_name_and_description(self):
        content = (
            "---\n"
            "name: open-browser\n"
            "description: Navigate to URLs\n"
            "---\n"
            "\n"
            "## Instructions\n"
            "Step 1"
        )
        metadata, body = parse_frontmatter(content)
        self.assertEqual(metadata["name"], "open-browser")
        self.assertEqual(metadata["description"], "Navigate to URLs")
        self.assertIn("## Instructions", body)

    # 2
    def test_parse_frontmatter_no_frontmatter(self):
        content = "Just plain content"
        metadata, body = parse_frontmatter(content)
        self.assertEqual(metadata, {})
        self.assertEqual(body, "Just plain content")

    # 3
    def test_parse_frontmatter_malformed_single_delimiter(self):
        content = "---\nname: foo\n"
        metadata, body = parse_frontmatter(content)
        self.assertEqual(metadata, {})
        self.assertEqual(body, content)

    # 4
    def test_discover_skills_finds_valid_skills(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "myskill"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                "---\n"
                "name: myskill\n"
                "description: A test skill\n"
                "---\n"
                "\n"
                "Do something useful",
                encoding="utf-8",
            )

            skills = discover_skills(tmpdir)
            self.assertEqual(len(skills), 1)
            self.assertEqual(skills[0].name, "myskill")
            self.assertEqual(skills[0].description, "A test skill")
            self.assertIn("Do something useful", skills[0].instructions)

    # 5
    def test_discover_skills_missing_dir(self):
        result = discover_skills("/nonexistent/path/xyz")
        self.assertEqual(result, [])

    # 6
    def test_discover_skills_skips_directories_without_skill_md(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "noskill"
            empty_dir.mkdir()

            skills = discover_skills(tmpdir)
            self.assertEqual(skills, [])

    # 7
    def test_skills_to_tools_generates_correct_format(self):
        skill = Skill(
            name="greeter",
            description="Say hello",
            instructions="Greet the user",
            directory=Path("/tmp/greeter"),
        )
        tools = skills_to_tools([skill])
        self.assertEqual(len(tools), 1)
        tool = tools[0]
        self.assertEqual(tool["type"], "function")
        self.assertEqual(tool["function"]["name"], "skill__greeter")
        self.assertEqual(tool["function"]["description"], "Say hello")
        self.assertEqual(
            tool["function"]["parameters"],
            {"type": "object", "properties": {}, "required": []},
        )

    # 8
    def test_load_skill_found_returns_instructions(self):
        skill = Skill(
            name="myskill",
            description="desc",
            instructions="Follow these steps",
            directory=Path("/tmp/myskill"),
        )
        result = load_skill([skill], "skill__myskill")
        self.assertEqual(result, "Follow these steps")

    # 9
    def test_load_skill_not_found_returns_error(self):
        skill = Skill(
            name="myskill",
            description="desc",
            instructions="steps",
            directory=Path("/tmp/myskill"),
        )
        result = load_skill([skill], "skill__unknown")
        self.assertIn("Unknown skill", result)
        self.assertIn("skill__unknown", result)


if __name__ == "__main__":
    unittest.main()
