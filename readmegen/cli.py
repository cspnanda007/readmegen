"""CLI entry point for ReadmeGen."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from readmegen import __version__
from readmegen.scanner import ProjectScanner
from readmegen.generator import ReadmeGenerator
from readmegen.config import load_config

console = Console()


@click.command()
@click.argument("project_path", default=".", type=click.Path(exists=True))
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["openai", "anthropic", "gemini"]),
    default=None,
    help="AI provider (auto-detected from env vars if not set).",
)
@click.option("--model", "-m", default=None, help="Model name override.")
@click.option(
    "--output",
    "-o",
    default="README.md",
    help="Output file name (default: README.md).",
)
@click.option(
    "--format",
    "-f",
    "fmt",
    type=click.Choice(["md", "rst"]),
    default="md",
    help="Output format.",
)
@click.option("--badges/--no-badges", default=True, help="Include badges.")
@click.option("--toc/--no-toc", default=True, help="Include table of contents.")
@click.option("--api-docs/--no-api-docs", default=True, help="Generate API docs.")
@click.option(
    "--contributing/--no-contributing",
    default=True,
    help="Include contributing section.",
)
@click.option("--license-section/--no-license-section", default=True, help="Include license.")
@click.option("--dry-run", is_flag=True, help="Preview without writing file.")
@click.option("--style", type=click.Choice(["professional", "casual", "minimal"]), default="professional", help="Writing style.")
@click.version_option(version=__version__)
def main(
    project_path,
    provider,
    model,
    output,
    fmt,
    badges,
    toc,
    api_docs,
    contributing,
    license_section,
    dry_run,
    style,
):
    """Generate a polished README for your project using AI.

    Scans PROJECT_PATH (default: current directory) to detect language,
    framework, dependencies, and structure, then generates a comprehensive
    README with badges, install instructions, usage examples, and more.

    Set OPENAI_API_KEY or ANTHROPIC_API_KEY or GOOGLE_API_KEY in your environment.
    """
    console.print(
        Panel(
            f"[bold blue]ReadmeGen v{__version__}[/bold blue]\n"
            "AI-powered README generator",
            expand=False,
        )
    )

    project = Path(project_path).resolve()

    # Load config from .readmegen.yml if it exists
    config = load_config(project)

    # CLI args override config file
    provider = provider or config.get("provider")
    model = model or config.get("model")
    style = style if style != "professional" else config.get("style", "professional")

    # Scan the project
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Scanning project...", total=None)
        scanner = ProjectScanner(project)
        scan_result = scanner.scan()

    console.print(f"\n[green]✓[/green] Detected: [bold]{scan_result.summary_line()}[/bold]")
    console.print(f"  Files scanned: {scan_result.total_files}")
    console.print(f"  Languages: {', '.join(scan_result.languages)}")
    if scan_result.framework:
        console.print(f"  Framework: {scan_result.framework}")

    # Generate README
    generator = ReadmeGenerator(provider=provider, model=model)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Generating README...", total=None)
        readme_content = generator.generate(
            scan_result=scan_result,
            output_format=fmt,
            include_badges=badges,
            include_toc=toc,
            include_api_docs=api_docs,
            include_contributing=contributing,
            include_license=license_section,
            style=style,
        )

    if dry_run:
        console.print("\n[yellow]── DRY RUN (not written to disk) ──[/yellow]\n")
        console.print(readme_content)
        return

    # Write output
    out_path = project / output
    if fmt == "rst":
        out_path = out_path.with_suffix(".rst")

    out_path.write_text(readme_content, encoding="utf-8")
    console.print(f"\n[green]✓[/green] README written to [bold]{out_path}[/bold]")
    console.print(f"  Size: {len(readme_content):,} characters")


if __name__ == "__main__":
    main()
