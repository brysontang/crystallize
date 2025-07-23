import argparse
import asyncio
import importlib.util
import inspect
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type

from rich.console import Console
from rich.table import Table
from simple_term_menu import TerminalMenu

from .experiments.experiment import Experiment
from .experiments.experiment_graph import ExperimentGraph
from .plugins.plugins import ArtifactPlugin

OBJ_TYPES = {
    "experiment": Experiment,
    "graph": ExperimentGraph,
}


def _import_module(file_path: Path, root_path: Path) -> Optional[Any]:
    """Import ``file_path`` as a module relative to ``root_path``."""
    try:
        relative_path = file_path.relative_to(root_path)
    except ValueError:
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                return module
            except Exception:
                return None
        return None

    module_name = ".".join(relative_path.with_suffix("").parts)

    try:
        if str(root_path) not in sys.path:
            sys.path.insert(0, str(root_path))

        return importlib.import_module(module_name)
    except Exception:
        return None


def discover_objects(directory: Path, obj_type: Type[Any]) -> Dict[str, Any]:
    # Use the current working directory as the root for module paths
    abs_directory = directory.resolve()
    root_path = Path.cwd()
    found: Dict[str, Any] = {}
    for file in abs_directory.rglob("*.py"):
        mod = _import_module(file, root_path)
        if not mod:
            continue
        for name, obj in inspect.getmembers(mod, lambda x: isinstance(x, obj_type)):
            try:
                rel = file.relative_to(root_path)
            except ValueError:
                rel = file
            found[f"{rel}:{name}"] = obj
    return found


def _select_from_menu(options: Sequence[str], title: str) -> Optional[int]:
    menu = TerminalMenu(options, title=title)
    idx = menu.show()
    return idx if idx is not None else None


def _multi_select(options: Sequence[str], title: str) -> Tuple[int, ...]:
    menu = TerminalMenu(
        options,
        title=title,
        multi_select=True,
        show_multi_select_hint=True,
        multi_select_select_on_accept=False,
    )
    idxs = menu.show()
    return idxs if idxs is not None else tuple()


def _confirm(msg: str) -> bool:
    resp = input(f"{msg} (y/N): ").strip().lower()
    return resp == "y"


async def _run_object(obj: Any, strategy: str, replicates: Optional[int]) -> Any:
    if isinstance(obj, ExperimentGraph):
        return await obj.arun(strategy=strategy, replicates=replicates)
    return await obj.arun(
        strategy=strategy,
        replicates=replicates,
        treatments=getattr(obj, "treatments", None),
        hypotheses=getattr(obj, "hypotheses", None),
    )


def _print_experiment_summary(result: Any) -> None:
    metrics = result.metrics
    treatments = list(metrics.treatments.keys())
    table = Table(title="Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", style="magenta")
    for t in treatments:
        table.add_column(t, style="green")
    metric_names = set(metrics.baseline.metrics)
    for t in treatments:
        metric_names.update(metrics.treatments[t].metrics)
    for name in sorted(metric_names):
        row = [name, str(metrics.baseline.metrics.get(name))]
        for t in treatments:
            row.append(str(metrics.treatments[t].metrics.get(name)))
        table.add_row(*row)
    console = Console()
    console.print(table)
    if result.errors:
        console.print("[bold red]Errors occurred[/]")
        for cond, err in result.errors.items():
            console.print(f"{cond}: {err}")


def _print_summary(result: Any) -> None:
    if isinstance(result, dict):
        for name, res in result.items():
            Console().print(f"[bold underline]{name}[/]")
            _print_experiment_summary(res)
    else:
        _print_experiment_summary(result)


async def run_async(args: argparse.Namespace) -> None:
    console = Console()
    obj_type = OBJ_TYPES[args.type]
    objects = discover_objects(Path(args.path), obj_type)
    if not objects:
        console.print("No objects found")
        return
    labels = list(objects.keys())
    idx = _select_from_menu(labels, f"Select {args.type}")
    if idx is None:
        return
    selected = objects[labels[idx]]

    if isinstance(selected, ExperimentGraph):
        deletable: List[Tuple[str, Path]] = []
        for node in selected._graph.nodes:
            exp: Experiment = selected._graph.nodes[node]["experiment"]
            plugin = exp.get_plugin(ArtifactPlugin)
            if not plugin or not exp.name:
                continue
            base = Path(plugin.root_dir) / exp.name
            if base.exists():
                deletable.append((node, base))
        if deletable:
            # Add an explicit option to skip deletion
            options = ["[ SKIP DELETION AND CONTINUE ]"] + [
                f"{name}: {path}" for name, path in deletable
            ]
            title = "Select data to DELETE (space to select, enter to confirm)"
            selected_indices = _multi_select(options, title)

            if not selected_indices:
                console.print(
                    "[yellow]No data selected for deletion. Continuing...[/yellow]"
                )
            # If user selected the SKIP option (index 0)
            elif 0 in selected_indices:
                console.print("[green]Keeping all data. Continuing...[/green]")
            else:
                # Adjust indices back by 1 since we added the SKIP option at the start
                paths_to_delete = [deletable[i - 1][1] for i in selected_indices]
                console.print(
                    "\n[bold yellow]The following directories will be PERMANENTLY DELETED:[/bold yellow]"
                )
                for p in paths_to_delete:
                    console.print(f"- {p}")

                if _confirm("\nAre you sure you want to proceed?"):
                    for p in paths_to_delete:
                        if args.dry_run:
                            console.print(
                                f"[cyan]DRY RUN: Would delete directory {p}[/cyan]"
                            )
                        else:
                            try:
                                shutil.rmtree(p)
                                console.print(f"[green]Deleted: {p}[/green]")
                            except OSError as e:
                                console.print(
                                    f"[bold red]Error deleting {p}: {e}[/bold red]"
                                )
                else:
                    console.print("[red]Deletion cancelled by user. Exiting.[/red]")
                    return

    strat_idx = _select_from_menu(["rerun", "resume"], "Execution strategy")
    if strat_idx is None:
        return
    strategy = ["rerun", "resume"][strat_idx]

    if args.dry_run:
        console.print(f"Would run {labels[idx]} with strategy {strategy}")
        return

    result = await _run_object(selected, strategy, args.replicates)
    _print_summary(result)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="crystallize")
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="Run experiment or graph")
    run_p.add_argument("type", choices=list(OBJ_TYPES), help="Object type")
    run_p.add_argument("--path", default=".", help="Search path")
    run_p.add_argument("--dry-run", action="store_true", help="Perform a dry run")
    run_p.add_argument(
        "--replicates", type=int, default=None, help="Override replicates"
    )
    return parser.parse_args(argv)


def run(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    if args.command == "run":
        asyncio.run(run_async(args))


if __name__ == "__main__":
    run()
