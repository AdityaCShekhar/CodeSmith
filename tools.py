"""File and shell command tools for the CLI."""

import os
import subprocess
import json
from pathlib import Path
from typing import Tuple, Optional


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


class ShellTools:
    """Handle shell command execution."""

    @staticmethod
    def run_command(command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Run a shell command and return output.
        
        Args:
            command: Shell command to run
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, return_code)
            
        Raises:
            ToolsError: If command execution fails
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            raise ToolsError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise ToolsError(f"Cannot run command: {str(e)}")

    @staticmethod
    def safe_command(command: str, timeout: int = 30) -> str:
        """Run a command safely and return formatted output.
        
        Args:
            command: Shell command to run
            timeout: Command timeout in seconds
            
        Returns:
            Formatted command output
        """
        stdout, stderr, code = ShellTools.run_command(command, timeout)
        
        output = []
        if stdout:
            output.append(f"STDOUT:\n{stdout}")
        if stderr:
            output.append(f"STDERR:\n{stderr}")
        if code != 0:
            output.append(f"Exit code: {code}")
        
        return "\n".join(output) if output else "✓ Command executed successfully"


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
