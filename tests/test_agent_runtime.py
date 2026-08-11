import asyncio

from codesmith.agent import AgentRuntime, ModelResponse, default_registry
from codesmith.context import discover_repository, load_rules
from codesmith.tools import Permission, RepositoryTools


class FakeModel:
    def __init__(self):
        self.calls = 0

    async def generate(self, messages, tools):
        self.calls += 1
        if self.calls == 1:
            return ModelResponse(tool_calls=[{"name": "read_file", "arguments": {"path": "hello.txt"}}])
        return ModelResponse(content="Inspected the file successfully.")


def test_agent_continues_after_tool_result(tmp_path):
    (tmp_path / "hello.txt").write_text("hello\n")
    runtime = AgentRuntime(FakeModel(), default_registry(RepositoryTools(tmp_path)))
    state = asyncio.run(runtime.run("Inspect hello.txt"))

    assert state.completed
    assert state.final_response == "Inspected the file successfully."
    assert state.files_read == {"hello.txt"}
    assert state.iteration == 2


def test_path_traversal_is_rejected(tmp_path):
    result = RepositoryTools(tmp_path).read_file("../secret.txt")
    assert not result.ok
    assert "outside repository" in result.output


def test_dangerous_command_is_blocked(tmp_path):
    result = RepositoryTools(tmp_path).run_command("rm -rf /")
    assert not result.ok
    assert result.permission == Permission.BLOCKED


def test_git_status_is_repository_scoped(tmp_path):
    result = RepositoryTools(tmp_path).git_status()
    assert result.metadata["command"] == "git status --short"


def test_tool_arguments_are_validated(tmp_path):
    registry = default_registry(RepositoryTools(tmp_path))
    result = asyncio.run(registry.execute("read_file", {}))
    assert not result.ok
    assert "required" in result.output


def test_unknown_tool_becomes_observation(tmp_path):
    registry = default_registry(RepositoryTools(tmp_path))
    result = asyncio.run(registry.execute("does_not_exist", {}))
    assert not result.ok
    assert "Unknown tool" in result.output


def test_repository_markers_are_discovered(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n")
    metadata = discover_repository(tmp_path)
    assert metadata.projects == {"python": ["pyproject.toml"]}


def test_project_rules_are_loaded(tmp_path):
    rules_dir = tmp_path / ".codesmith"
    rules_dir.mkdir()
    (rules_dir / "rules.md").write_text("Use pytest.\n")
    assert load_rules(tmp_path) == "Use pytest.\n"
