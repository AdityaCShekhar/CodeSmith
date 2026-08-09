"""File and context tools for the CLI."""

from pathlib import Path
from typing import Optional


class ToolsError(Exception):
    """Custom exception for tool operations."""
    pass


class FileTools:
    """Handle file operations."""

    @staticmethod
    def read_file(filepath: str) -> str:
        """Read a file and return its contents.
        
        Args:
            filepath: Path to the file to read
            
        Returns:
            File contents as string
            
        Raises:
            ToolsError: If file doesn't exist or can't be read
        """
        try:
            path = Path(filepath).resolve()
            if not path.exists():
                raise ToolsError(f"File not found: {filepath}")
            if not path.is_file():
                raise ToolsError(f"Path is not a file: {filepath}")
            return path.read_text()
        except Exception as e:
            raise ToolsError(f"Cannot read file '{filepath}': {str(e)}")

    @staticmethod
    def write_file(filepath: str, content: str) -> str:
        """Write content to a file.
        
        Args:
            filepath: Path to the file to write
            content: Content to write
            
        Returns:
            Success message
            
        Raises:
            ToolsError: If file can't be written
        """
        try:
            path = Path(filepath).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return f"✓ Successfully wrote {len(content)} bytes to {filepath}"
        except Exception as e:
            raise ToolsError(f"Cannot write file '{filepath}': {str(e)}")

    @staticmethod
    def file_info(filepath: str) -> dict:
        """Get information about a file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Dictionary with file info
        """
        try:
            path = Path(filepath).resolve()
            if not path.exists():
                raise ToolsError(f"File not found: {filepath}")
            stat = path.stat()
            return {
                "path": str(path),
                "size": stat.st_size,
                "exists": True,
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
            }
        except Exception as e:
            raise ToolsError(f"Cannot get file info: {str(e)}")


class ContextInjector:
    """Inject file context into prompts."""

    @staticmethod
    def inject_files(prompt: str, file_paths: Optional[list] = None) -> str:
        """Inject file contents into the prompt.
        
        Args:
            prompt: Original prompt
            file_paths: List of file paths to include
            
        Returns:
            Enhanced prompt with file context
        """
        if not file_paths:
            return prompt

        context = []
        for filepath in file_paths:
            try:
                content = FileTools.read_file(filepath)
                context.append(f"File: {filepath}\n```\n{content}\n```")
            except ToolsError as e:
                context.append(f"Error reading {filepath}: {str(e)}")

        if context:
            injected = "Context files:\n" + "\n\n".join(context) + "\n\nPrompt:\n" + prompt
            return injected
        return prompt
