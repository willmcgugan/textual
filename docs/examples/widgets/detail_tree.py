from rich.text import Text

from textual.app import App, ComposeResult
from textual.widgets import Tree


class TreeApp(App):
    def compose(self) -> ComposeResult:
        tree: Tree[dict] = Tree("A bit of everything")
        tree.root.expand()
        fruit = tree.root.add("Fruit", expand=True)
        fruit.add_leaf("Orange", detail="🍊")
        fruit.add_leaf("Apple", detail="🍎")
        fruit.add_leaf("Banana", detail=":banana:")
        fruit.add_leaf("Pear", detail="🍐")

        # https://en.wikipedia.org/wiki/Demographics_of_the_United_Kingdom
        pop = tree.root.add("Population", expand=True)
        uk = pop.add("United Kingdom", expand=True, detail="67,081,234")
        uk.add_leaf("England", detail="56,550,138")
        uk.add_leaf("Scotland", detail="5,466,000")
        uk.add_leaf("Wales", detail="3,169,586")
        uk.add_leaf("Northern Ireland", detail="1,895,510")

        # https://en.wikipedia.org/wiki/List_of_countries_by_average_yearly_temperature
        temps = tree.root.add("Average Temperatures", expand=True)
        temps.add_leaf("Burkina Faso", detail=Text("30.40 °C", style="red"))
        temps.add_leaf("New Zealand", detail="[red]10.46 °C[/red]")
        temps.add_leaf("Canada", detail="[blue]-4.03 °C[/blue]")
        temps.add_leaf("Greenland", detail=Text("-18.68 °C", style="blue"))

        yield tree


if __name__ == "__main__":
    app = TreeApp()
    app.run()
