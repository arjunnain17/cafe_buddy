# app.py

import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.markdown import Markdown


from core.reccomend import load_indexes
from core.agent import build_agent, invoke_agent
from core.basket import (
    view_basket, clear_basket,
    set_budget, checkout, set_dietary
)

load_dotenv()
console = Console()


# ── Slash command handler ─────────────────────────────────────────────────────

def handle_slash(command: str, agent) -> bool:
    """
    Handles slash commands directly without hitting the agent.
    Returns True if command was handled, False if not a slash command.
    """
    cmd = command.strip().lower()

    if cmd == "/help":
        console.print(Panel(
            "[yellow]/basket[/yellow]          Show current order\n"
            "[yellow]/budget <amount>[/yellow]  Set your budget e.g. /budget 500\n"
            "[yellow]/diet <pref>[/yellow]      Set dietary preference e.g. /diet vegan\n"
            "[yellow]/checkout[/yellow]         Finalise order and print receipt\n"
            "[yellow]/clear[/yellow]            Clear basket — keeps budget and dietary\n"
            "[yellow]/reset[/yellow]            Clear everything including budget and dietary\n"
            "[yellow]/verbose[/yellow]          Toggle tool reasoning visibility\n"
            "[yellow]/help[/yellow]             Show this help message\n"
            "[yellow]/quit[/yellow]             Exit Cafe Buddy",
            title="[cyan]Commands[/cyan]",
            border_style="cyan",
        ))
        return True

    if cmd == "/basket":
        result = view_basket()
        console.print(Panel(result, title="🛒 Your Basket", border_style="green"))
        return True

    if cmd.startswith("/budget "):
        amount = cmd.split(" ", 1)[1].replace("₹", "").strip()
        try:
            set_budget(float(amount))
            console.print(f"[green]✓ Budget set to ₹{float(amount):.0f}[/green]")
        except ValueError:
            console.print(f"[red]Invalid amount: '{amount}'[/red]")
        return True

    if cmd.startswith("/diet "):
        pref = cmd.split(" ", 1)[1].strip()
        set_dietary([pref])
        console.print(f"[green]✓ Dietary preference set: {pref}[/green]")
        return True

    if cmd == "/checkout":
        result = checkout()
        console.print(Panel(result, title="Receipt", border_style="bright_yellow"))
        return True

    if cmd == "/clear":
        clear_basket()
        console.print("[yellow]Basket cleared ☕[/yellow]")
        return True

    if cmd == "/reset":
        from core.basket import _basket, _budget, _dietary, _item_counter
        clear_basket()
        import core.basket as b
        b._budget  = None
        b._dietary = []
        console.print("[yellow]Session reset — basket, budget and dietary cleared.[/yellow]")
        return True

    if cmd == "/verbose":
        # stored as app-level flag — toggled each call
        app_state["verbose"] = not app_state.get("verbose", False)
        state = "ON" if app_state["verbose"] else "OFF"
        console.print(f"[dim]Verbose mode: {state}[/dim]")
        return True

    if cmd in ("/quit", "/exit", "/q"):
        console.print("\n[bold]Thanks for visiting Dohful! ☕ See you soon.[/bold]")
        raise SystemExit(0)

    if cmd.startswith("/"):
        console.print(f"[red]Unknown command '{cmd}'. Type /help for options.[/red]")
        return True

    return False


# ── App state ─────────────────────────────────────────────────────────────────

app_state = {"verbose": False}


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    # load indexes once at startup
    load_indexes()

    # build agent
    agent = build_agent()

    # welcome banner
    console.print(Panel(
        Text.assemble(
            ("☕  Welcome to Dohful\n\n", "bold cyan"),
            ("Hi! I'm Heer, your barista today.\n", ""),
            ("Tell me what you're in the mood for,\n", "dim"),
            ("or type ", "dim"),
            ("/help", "yellow"),
            (" for commands.", "dim"),
        ),
        border_style="cyan",
        padding=(1, 4),
    ))

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold]Goodbye! ☕[/bold]")
            break

        if not user_input:
            continue

        # handle slash commands first
        if handle_slash(user_input, agent):
            continue

        # pass to agent
        try:
            with console.status(
                "[dim]Heer is thinking...[/dim]", spinner="dots"
            ):
                reply = invoke_agent(agent, user_input)

            console.print("\n[bold cyan]Heer:[/bold cyan]")
            console.print(Markdown(reply))

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()