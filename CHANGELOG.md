# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## Unreleased

### Added

- Added support for a detail column to the Tree widget https://github.com/Textualize/textual/pull/5096

## [0.83.0] - 2024-10-10

### Added

- Added support for A-F to Digits widget https://github.com/Textualize/textual/pull/5094
- Added `Region.constrain` https://github.com/Textualize/textual/pull/5097

### Changed

- `Screen.ALLOW_IN_MAXIMIZED_VIEW` will now default to `App.ALLOW_IN_MAXIMIZED_VIEW` https://github.com/Textualize/textual/pull/5088
- Widgets matching `.-textual-system` will now be included in the maximize view by default https://github.com/Textualize/textual/pull/5088
- Digits are now thin by default, style with text-style: bold to get bold digits https://github.com/Textualize/textual/pull/5094
- Made `Widget.absolute_offset` public https://github.com/Textualize/textual/pull/5097
- Tooltips are now displayed directly below the mouse cursor https://github.com/Textualize/textual/pull/5097
- `Region.inflect` will now assume that margins overlap https://github.com/Textualize/textual/pull/5097
- `Pilot.click` and friends will now accept a widget, in addition to a selector https://github.com/Textualize/textual/pull/5095

## [0.82.0] - 2024-10-03

### Fixed

- Fixed issue with screen not updating when auto_refresh was enabled https://github.com/Textualize/textual/pull/5063
- Fixed issues regarding loading indicator https://github.com/Textualize/textual/pull/5079
- Fixed issues with inspecting the lazy loaded widgets module https://github.com/Textualize/textual/pull/5080

### Added

- Added `DOMNode.is_on_screen` property https://github.com/Textualize/textual/pull/5063
- Added support for keymaps (user configurable key bindings) https://github.com/Textualize/textual/pull/5038
- Added descriptions to bindings for all internal widgets, and updated casing to be consistent https://github.com/Textualize/textual/pull/5062

### Changed

- Breaking change: `Widget.set_loading` no longer return an awaitable https://github.com/Textualize/textual/pull/5079

## [0.81.0] - 2024-09-25

### Added

- Added `x_axis` and `y_axis` parameters to `Widget.scroll_to_region` https://github.com/Textualize/textual/pull/5047
- Added `Tree.move_cursor_to_line` https://github.com/Textualize/textual/pull/5052
- Added `Screen.pop_until_active` https://github.com/Textualize/textual/pull/5069

### Changed

- Tree will no longer scroll the X axis when moving the cursor https://github.com/Textualize/textual/pull/5047
- DirectoryTree will no longer select the first node https://github.com/Textualize/textual/pull/5052

### Fixed

- Fixed widgets occasionally not getting Resize events https://github.com/Textualize/textual/pull/5048
- Fixed tree regression https://github.com/Textualize/textual/pull/5052
- Fixed glitch with single line inline widget https://github.com/Textualize/textual/pull/5054

## [0.80.1] - 2024-09-24

### Fixed

- Fixed crash when exiting the app prematurely https://github.com/Textualize/textual/pull/5039
- Fixed exception constructing TextArea outside of App https://github.com/Textualize/textual/pull/5045

## [0.80.0] - 2024-09-23

### Added

- Added `MaskedInput` widget https://github.com/Textualize/textual/pull/4783
- Input validation for floats and integers accept embedded underscores, e.g., "1_234_567" is valid. https://github.com/Textualize/textual/pull/4784
- Support for `"none"` value added to `dock`, `hatch` and `split` styles https://github.com/Textualize/textual/pull/4982
- Support for `"none"` added to box and border style properties (e.g `widget.style.border = "none"`) https://github.com/Textualize/textual/pull/4982
- Docstrings added to most style properties https://github.com/Textualize/textual/pull/4982
- Added `ansi_color` switch to App to permit ANSI (themed) colors https://github.com/Textualize/textual/pull/5000
- Added `:ansi` pseudo class https://github.com/Textualize/textual/pull/5000
- Added `-ansi-scrollbar` style to widgets https://github.com/Textualize/textual/pull/5000
- Added `App.INLINE_PADDING` to define the number of spaces above inline apps https://github.com/Textualize/textual/pull/5000
- Added `nocolor` psuedoclass when NO_COLOR env var is set- `BINDING_GROUP_TITLE` now defaults to `None` https://github.com/Textualize/textual/pull/5023
- Added `TreeNode.siblings`, `TreeNode.next_sibling`, `TreeNode.previous_sibling`, `TreeNode.is_collapsed` https://github.com/Textualize/textual/pull/5023
- Added additional bindings to Tree widget https://github.com/Textualize/textual/pull/5023
- Added `Tree.center_scroll` https://github.com/Textualize/textual/pull/5023
- Added `Tree.unselect` https://github.com/Textualize/textual/pull/5023


### Changed

- Input validation for integers no longer accepts scientific notation like '1.5e2'; must be castable to int. https://github.com/Textualize/textual/pull/4784
- Default `scrollbar-size-vertical` changed to `2` in inline styles to match Widget default CSS (unlikely to affect users) https://github.com/Textualize/textual/pull/4982
- Removed border-right from `Toast` https://github.com/Textualize/textual/pull/4984
- Some fixes in `RichLog` result in slightly different semantics, see docstrings for details https://github.com/Textualize/textual/pull/4978
- Changed how scrollbars are rendered (will have no visual effect, but will break snapshot tests) https://github.com/Textualize/textual/pull/5000
- Added `enabled` switch to filters (mostly used internally) https://github.com/Textualize/textual/pull/5000
- `BINDING_GROUP_TITLE` now defaults to `None` https://github.com/Textualize/textual/pull/5023
- Breaking change: Changed how scrollbars are rendered so they work in ansi mode (will break snapshots) https://github.com/Textualize/textual/pull/5023

### Fixed

- Input validation of floats no longer accepts NaN (not a number). https://github.com/Textualize/textual/pull/4784
- Fixed issues with screenshots by simplifying segments only for snapshot tests https://github.com/Textualize/textual/issues/4929
- Fixed `RichLog.write` not respecting `width` parameter https://github.com/Textualize/textual/pull/4978
- Fixed `RichLog` writing at wrong width when `write` occurs before width is known (e.g. in `compose` or `on_mount`) https://github.com/Textualize/textual/pull/4978
- Fixed `RichLog.write` incorrectly shrinking width to `RichLog.min_width` when `shrink=True` (now shrinks to fit content area instead) https://github.com/Textualize/textual/pull/4978
- Fixed flicker when setting `dark` reactive on startup https://github.com/Textualize/textual/pull/4989
- Fixed command palette not sorting search results by their match score https://github.com/Textualize/textual/pull/4994
- Fixed `DataTable` cached height issue on re-populating the table when using auto-height rows https://github.com/Textualize/textual/pull/4992
- Fixed inline app output being cleared when `inline_no_clear=True` https://github.com/Textualize/textual/issues/5019

## [0.79.1] - 2024-08-31

### Fixed

- Fixed broken updates when non active screen changes https://github.com/Textualize/textual/pull/4957

## [0.79.0] - 2024-08-30

### Added

- Added `DOMNode.check_consume_key` https://github.com/Textualize/textual/pull/4940
- Added `App.ESCAPE_TO_MINIMIZE`, `App.screen_to_minimize`, and `Screen.ESCAPE_TO_MINIMIZE` https://github.com/Textualize/textual/pull/4951
- Added `DOMNode.query_exactly_one` https://github.com/Textualize/textual/pull/4950
- Added `SelectorSet.is_simple` https://github.com/Textualize/textual/pull/4950

### Changed

- KeyPanel will show multiple keys if bound to the same action https://github.com/Textualize/textual/pull/4940
- Breaking change: `DOMNode.query_one` will not `raise TooManyMatches` https://github.com/Textualize/textual/pull/4950

## [0.78.0] - 2024-08-27

### Added

- Added Maximize and Minimize system commands. https://github.com/Textualize/textual/pull/4931
- Added `Screen.maximize`, `Screen.minimize`, `Screen.action_maximize`, `Screen.action_minimize`, `Widget.is_maximized`, `Widget.allow_maximize`. https://github.com/Textualize/textual/pull/4931
- Added `Widget.ALLOW_MAXIMIZE`, `Screen.ALLOW_IN_MAXIMIZED_VIEW` classvars https://github.com/Textualize/textual/pull/4931

## [0.77.0] - 2024-08-22

### Added

- Added `tooltip` to Binding https://github.com/Textualize/textual/pull/4859
- Added a link to the command palette to the Footer (set `show_command_palette=False` to disable) https://github.com/Textualize/textual/pull/4867
- Added `TOOLTIP_DELAY` to App to customize time until a tooltip is displayed
- Added "Show keys" option to system commands to show a summary of key bindings. https://github.com/Textualize/textual/pull/4876
- Added "split" CSS style, currently undocumented, and may change. https://github.com/Textualize/textual/pull/4876
- Added `Region.get_spacing_between` https://github.com/Textualize/textual/pull/4876
- Added `App.COMMAND_PALETTE_KEY` to change default command palette key binding https://github.com/Textualize/textual/pull/4867
- Added `App.get_key_display` https://github.com/Textualize/textual/pull/4890
- Added `DOMNode.BINDING_GROUP` https://github.com/Textualize/textual/pull/4906
- Added `DOMNode.HELP` classvar which contains Markdown help to be shown in the help panel https://github.com/Textualize/textual/pull/4915
- Added `App.get_system_commands` https://github.com/Textualize/textual/pull/4920
- Added "Save Screenshot" system command https://github.com/Textualize/textual/pull/4922

### Changed

- Removed caps_lock and num_lock modifiers https://github.com/Textualize/textual/pull/4861 
- Keys such as escape and space are now displayed in lower case in footer https://github.com/Textualize/textual/pull/4876
- Changed default command palette binding to `ctrl+p` https://github.com/Textualize/textual/pull/4867
- Removed `ctrl_to_caret` and `upper_case_keys` from Footer. These can be implemented in `App.get_key_display`.
- Renamed `SystemCommands` to `SystemCommandsProvider` https://github.com/Textualize/textual/pull/4920
- Breaking change: Removed `ClassicFooter` widget (please use new `Footer` widget) https://github.com/Textualize/textual/pull/4921
- Disallowed `Screen` instances in `App.SCREENS` and `App.MODES`

### Fixed

- Fix crash when `validate_on` value isn't a set https://github.com/Textualize/textual/pull/4868
- Fix `Input.cursor_blink` having no effect on the blink cycle after mounting https://github.com/Textualize/textual/pull/4869
- Fixed scrolling by page not taking scrollbar in to account https://github.com/Textualize/textual/pull/4916
- Fixed `App.MODES` being the same for all instances -- per-instance modes now exist internally

## [0.76.0]

### Changed

- Input cursor will no longer jump to the end on focus https://github.com/Textualize/textual/pull/4773
- Removed `Size.cip_size`, which was a clone of `crop_size`
- Widgets with auto dimensions will now grow if there is a scrollbar https://github.com/Textualize/textual/pull/4844
- Don't do automatic refresh when widget is not visible https://github.com/Textualize/textual/pull/4847
- Renamed `DOMNode._automatic_refresh` to `DOMNode.automatic_refresh` to allow for customization https://github.com/Textualize/textual/pull/4847

### Fixed

- Input cursor blink effect will now restart correctly when any action is performed on the input https://github.com/Textualize/textual/pull/4773
- Fixed bindings on same key not updating description https://github.com/Textualize/textual/pull/4850

### Added

- Textual will use the `ESCDELAY` env var when detecting escape keys https://github.com/Textualize/textual/pull/4848

## [0.75.1] - 2024-08-02

### Fixed

- Fixed issue with Enter events causing unresponsive UI https://github.com/Textualize/textual/pull/4833


## [0.75.0] - 2024-08-01

### Added

- Added `App.open_url` to open URLs in the web browser. When running via the WebDriver, the URL will be opened in the browser that is controlling the app https://github.com/Textualize/textual/pull/4819
- Added `Widget.is_mouse_over` https://github.com/Textualize/textual/pull/4818
- Added `node` attribute to `events.Enter` and `events.Leave` https://github.com/Textualize/textual/pull/4818

### Changed

- `events.Enter` and `events.Leave` events now bubble. https://github.com/Textualize/textual/pull/4818
- Renamed `Widget.mouse_over` to `Widget.mouse_hover` https://github.com/Textualize/textual/pull/4818

### Fixed

- Fixed issue with `mutate_reactive` and data binding https://github.com/Textualize/textual/pull/4828

## [0.74.0] - 2024-07-25

### Fixed

- Fixed issues in Kitty terminal after exiting app https://github.com/Textualize/textual/issues/4779
- Fixed exception when removing Selects https://github.com/Textualize/textual/pull/4786
- Fixed issue with non-clickable Footer keys https://github.com/Textualize/textual/pull/4798
- Fixed issue with recompose not working from Mount handler https://github.com/Textualize/textual/pull/4802

### Changed

- Calling `Screen.dismiss` with no arguments will invoke the screen callback with `None` (previously the callback wasn't invoke at all). https://github.com/Textualize/textual/pull/4795

## [0.73.0] - 2024-07-18

### Added

- Added `TextArea.line_number_start` reactive attribute https://github.com/Textualize/textual/pull/4471
- Added `TextArea.matching_bracket_location` property https://github.com/Textualize/textual/pull/4764
- Added `DOMNode.mutate_reactive` https://github.com/Textualize/textual/pull/4731
- Added "quality" parameter to `textual.color.Gradient` https://github.com/Textualize/textual/pull/4739
- Added `textual.color.Gradient.get_rich_color` https://github.com/Textualize/textual/pull/4739
- `Widget.remove_children` now accepts an iterable if widgets in addition to a selector https://github.com/Textualize/textual/issues/4735
- Raise `ValueError` with improved error message when number of cells inserted using `DataTable.add_row` doesn't match the number of columns in the table https://github.com/Textualize/textual/pull/4742
- Add `Tree.move_cursor` to programmatically move the cursor without selecting the node https://github.com/Textualize/textual/pull/4753
- Added `Footer` component style handling of padding for the key/description https://github.com/Textualize/textual/pull/4651
- `StringKey` is now exported from `data_table` https://github.com/Textualize/textual/pull/4760
- `TreeNode.add` and `TreeNode.add_leaf` now accepts `before` and `after` arguments to position a new node https://github.com/Textualize/textual/pull/4772
- Added a `gradient` parameter to the `ProgressBar` widget https://github.com/Textualize/textual/pull/4774

### Fixed

- Fixed issue with `Tabs` where disabled tabs could still be activated by clicking the underline https://github.com/Textualize/textual/issues/4701
- Fixed scroll_visible with margin https://github.com/Textualize/textual/pull/4719
- Fixed programmatically disabling button stuck in hover state https://github.com/Textualize/textual/pull/4724
- Fixed `DataTable` poor performance on startup and focus change when rows contain multi-line content https://github.com/Textualize/textual/pull/4748
- Fixed `Tree` and `DirectoryTree` horizontal scrolling off-by-2 https://github.com/Textualize/textual/pull/4744
- Fixed text-opacity in component styles https://github.com/Textualize/textual/pull/4747
- Ensure `Tree.select_node` sends `NodeSelected` message https://github.com/Textualize/textual/pull/4753
- Fixed message handlers not working when message types are assigned as the value of class vars https://github.com/Textualize/textual/pull/3940
- Fixed `CommandPalette` not focusing the input when opened when `App.AUTO_FOCUS` doesn't match the input https://github.com/Textualize/textual/pull/4763
- `SelectionList.SelectionToggled` will now be sent for each option when a bulk toggle is performed (e.g. `toggle_all`). Previously no messages were sent at all. https://github.com/Textualize/textual/pull/4759
- Fixed focus styles not being updated on blur https://github.com/Textualize/textual/pull/4771

### Changed

- "Discover" hits in the command palette are no longer sorted alphabetically https://github.com/Textualize/textual/pull/4720
- `TreeNodeSelected` messages are now posted before `TreeNodeExpanded` messages
when an expandable node is selected https://github.com/Textualize/textual/pull/4753
- `Markdown.LinkClicked.href` is now automatically unquoted https://github.com/Textualize/textual/pull/4749
- The mouse cursor hover effect of `Tree` and `DirectoryTree` will no longer linger after the mouse leaves the widget https://github.com/Textualize/textual/pull/4766


## [0.72.0] - 2024-07-09

### Changed

- More predictable DOM removals. https://github.com/Textualize/textual/pull/4708

### Fixed

- Fixed clicking separator in OptionList moving cursor https://github.com/Textualize/textual/issues/4710
- Fixed scrolling issue in OptionList https://github.com/Textualize/textual/pull/4709

## [0.71.0] - 2024-06-29

### Changed

- Snapshot tests will normalize SVG output so that changes with no visual impact don't break snapshots, but this release will break most of them.
- Breaking change: `App.push_screen` now returns an Awaitable rather than a screen. https://github.com/Textualize/textual/pull/4672
- Breaking change: `Screen.dismiss` now returns an Awaitable rather than a bool. https://github.com/Textualize/textual/pull/4672

### Fixed

- Fixed grid + keyline when the grid has auto dimensions https://github.com/Textualize/textual/pull/4680
- Fixed mouse code leakage https://github.com/Textualize/textual/pull/4681
- Fixed link inside markdown table not posting a `Markdown.LinkClicked` message https://github.com/Textualize/textual/issues/4683
- Fixed issue with mouse movements on non-active screen https://github.com/Textualize/textual/pull/4688

## [0.70.0] - 2024-06-19

### Fixed

- Fixed erroneous mouse 'ButtonDown' reporting for mouse movement when any-event mode is enabled in xterm. https://github.com/Textualize/textual/pull/3647

## [0.69.0] - 2024-06-16

### Added

- Added `App.simulate_key` https://github.com/Textualize/textual/pull/4657

### Fixed

- Fixed issue with pop_screen launched from an action https://github.com/Textualize/textual/pull/4657

### Changed

- `App.check_bindings` is now private
- `App.action_check_bindings` is now `App.action_simulate_key`

## [0.68.0] - 2024-06-14

### Added

- Added `ContentSwitcher.add_content`

### Fixed

- Improved handling of non-tty input https://github.com/Textualize/textual/pull/4647

## [0.67.1] - 2024-06-12

### Changed

- Reverts Vim keys in DataTable, provides alternatives https://github.com/Textualize/textual/pull/4638

## [0.67.0] - 2024-06-11

### Added

- Added support for Kitty's key protocol https://github.com/Textualize/textual/pull/4631
- `ctrl+pageup`/`ctrl+pagedown` will scroll page left/right in DataTable https://github.com/Textualize/textual/pull/4633
- `g`/`G` will scroll to the top/bottom of the DataTable https://github.com/Textualize/textual/pull/4633
- Added simple `hjkl` key bindings to move the cursor in DataTable https://github.com/Textualize/textual/pull/4633

### Changed

- `home` and `end` now works horizontally instead of vertically in DataTable https://github.com/Textualize/textual/pull/4633
- `Tree` and `DirectoryTree` nodes now have a bigger click target, spanning the full line https://github.com/Textualize/textual/pull/4636

### Fixed

- Fixed pageup/pagedown behavior in DataTable https://github.com/Textualize/textual/pull/4633
- Added `App.CLOSE_TIMEOUT` https://github.com/Textualize/textual/pull/4635
- Fixed deadlock on shutdown https://github.com/Textualize/textual/pull/4635

## [0.66.0] - 2024-06-08

### Changed

- `get_content_height` will now return 0 if the renderable is Falsey https://github.com/Textualize/textual/pull/4617
- Buttons may not be pressed within their "active_effect_duration" to prevent inadvertent activations https://github.com/Textualize/textual/pull/4621
- `Screen.dismiss` is now a noop if the screen isn't active. Previously it would raise a `ScreenStackError`, now it returns `False`. https://github.com/Textualize/textual/pull/4621
- Increased window for escape processing to 100ms https://github.com/Textualize/textual/pull/4625
- Tooltips are now hidden when any key is pressed https://github.com/Textualize/textual/pull/4625

### Added

- Added `Screen.is_active` 
- Added `icon` reactive to Header widget https://github.com/Textualize/textual/pull/4627
- Added `time_format` reactive to Header widget https://github.com/Textualize/textual/pull/4627
- Added `tooltip` parameter to input widgets https://github.com/Textualize/textual/pull/4625

## [0.65.2] - 2024-06-06

### Fixed

- Fixed issue with notifications and screen switches https://github.com/Textualize/textual/pull/4615

### Added

- Added textual.rlock.RLock https://github.com/Textualize/textual/pull/4615

## [0.65.1] - 2024-06-05

### Fixed

- Fixed hot reloading with hatch rule https://github.com/Textualize/textual/pull/4606
- Fixed hatch style parsing https://github.com/Textualize/textual/pull/4606

## [0.65.0] - 2024-06-05

### Added

- Added Command Palette Opened, Closed, and OptionHighlighted events https://github.com/Textualize/textual/pull/4600
- Added hatch style https://github.com/Textualize/textual/pull/4603

### Fixed

- Fixed DataTable cursor flicker on scroll https://github.com/Textualize/textual/pull/4598

### Changes

- TabbedContent will automatically make tabs active when a widget in a pane is focused https://github.com/Textualize/textual/issues/4593

## [0.64.0] - 2024-06-03

### Fixed

- Fix traceback on exit https://github.com/Textualize/textual/pull/4575
- Fixed `Markdown.goto_anchor` no longer scrolling the heading into view https://github.com/Textualize/textual/pull/4583
- Fixed Footer flicker on initial focus https://github.com/Textualize/textual/issues/4573

## [0.63.6] - 2024-05-29

### Fixed

- Fixed issue with bindings not refreshing https://github.com/Textualize/textual/pull/4571

## [0.63.5] - 2024-05-28

### Fixed

- Fixed data table disappearing from tabs https://github.com/Textualize/textual/pull/4567

### Added

- Added `Styles.is_auto_width` and `Style.is_auto_height`

## [0.63.4] - 2024-05-26

### Added

- Added `immediate` switch to `Signal.publish`

### Fixed

- Fixed freeze in recompose from bindings https://github.com/Textualize/textual/pull/4558

## [0.63.3] - 2024-05-24

### Fixed

- Fixed `Footer` grid size https://github.com/Textualize/textual/pull/4545
- Fixed bindings not updated on auto focus https://github.com/Textualize/textual/pull/4551

### Changed

- Attempting to mount on a non-mounted widget now raises a MountError https://github.com/Textualize/textual/pull/4547

## [0.63.2] - 2024-05-23

### Fixed

- Fixed issue with namespaces in links https://github.com/Textualize/textual/pull/4546

## [0.63.1] - 2024-05-22

### Fixed

- Fixed display of multiple bindings https://github.com/Textualize/textual/pull/4543

## [0.63.0] - 2024-05-22

### Fixed

- Fixed actions in links https://github.com/Textualize/textual/pull/4540

### Changed

- Breaking change: New Footer (likely a drop in replacement, unless you have customized styles) https://github.com/Textualize/textual/pull/4537
- Stylistic changes to Markdown (simpler headers, less margin, etc) https://github.com/Textualize/textual/pull/4541

## [0.62.0] - 2024-05-20

### Added

- Added `start` and `end` properties to Markdown Navigator
- Added `Widget.anchor`, `Widget.clear_anchor`, and `Widget.is_anchored` https://github.com/Textualize/textual/pull/4530

## [0.61.1] - 2024-05-19

### Fixed

- Fixed auto grid columns ignoring gutter https://github.com/Textualize/textual/issues/4522

## [0.61.0] - 2024-05-18

### Added

- Added `App.get_default_screen` https://github.com/Textualize/textual/pull/4520
- Added dynamic binding via `DOMNode.check_action` https://github.com/Textualize/textual/pull/4516
- Added `"focused"` action namespace so you can bind a key to an action on the focused widget https://github.com/Textualize/textual/pull/4516
- Added "focused" to allowed action namespaces https://github.com/Textualize/textual/pull/4516

### Changed

- Breaking change: Actions (as used in bindings) will no longer check the app if they are unhandled. This was undocumented anyway, and not that useful. https://github.com/Textualize/textual/pull/4516
- Breaking change: Renamed `App.namespace_bindings` to `active_bindings`


## [0.60.1] - 2024-05-15

### Fixed

- Dependency issue

## [0.60.0] - 2024-05-14

### Fixed

- Fixed auto width not working for option lists https://github.com/Textualize/textual/pull/4507

### Added

- Added `DOMNode.query_children` https://github.com/Textualize/textual/pull/4508

## [0.59.0] - 2024-05-11

### Fixed

- Fixed `SelectionList` issues after removing an option https://github.com/Textualize/textual/pull/4464
- Fixed `ListView` bugs with the initial index https://github.com/Textualize/textual/pull/4452
- Fixed `Select` not closing https://github.com/Textualize/textual/pull/4499
- Fixed setting `loading=False` removing all child loading indicators https://github.com/Textualize/textual/pull/4499

### Changed

- When displaying a message using `App.exit()`, the console no longer highlights things such as numbers.

### Added

- Added `message_signal` to MessagePump, to listen to events sent to another widget. https://github.com/Textualize/textual/pull/4487
- Added `Widget.suppress_click` https://github.com/Textualize/textual/pull/4499

## [0.58.1] - 2024-05-01

### Fixed

- Fixed issue with Markdown mounting content lazily https://github.com/Textualize/textual/pull/4466
- Fixed intermittent issue with scrolling to focus https://github.com/Textualize/textual/commit/567caf8acb196260adf6a0a6250e3ff5093056d0
- Fixed issue with scrolling to center https://github.com/Textualize/textual/pull/4469


## [0.58.0] - 2024-04-25

### Fixed

- Fixed `TextArea` to end mouse selection only if currently selecting https://github.com/Textualize/textual/pull/4436
- Fixed issue with scroll_to_widget https://github.com/Textualize/textual/pull/4446
- Fixed issue with margins https://github.com/Textualize/textual/pull/4441

### Changed

- Added argument to signal callbacks https://github.com/Textualize/textual/pull/4438

## [0.57.1] - 2024-04-20

### Fixed

- Fixed an off-by-one error in the line number of the `Document.end` property https://github.com/Textualize/textual/issues/4426
- Fixed setting scrollbar colors not updating the scrollbar https://github.com/Textualize/textual/pull/4433
- Fixed flushing in inline mode https://github.com/Textualize/textual/pull/4435

### Added

- Added `Offset.clamp` and `Size.clamp_offset` https://github.com/Textualize/textual/pull/4435


## [0.57.0] - 2024-04-19

### Fixed

- Fixed `Integer` validator missing failure description when not a number https://github.com/Textualize/textual/issues/4413
- Fixed a crash in `DataTable` if you clicked a link in the border https://github.com/Textualize/textual/issues/4410
- Fixed issue with cursor position https://github.com/Textualize/textual/pull/4429

### Added

- Added `App.copy_to_clipboard` https://github.com/Textualize/textual/pull/4416

## [0.56.4] - 2024-04-09

### Fixed

- Disabled terminal synchronization in inline mode as it breaks on some terminals

## [0.56.3] - 2024-04-08

### Fixed

- Fixed inline mode not updating https://github.com/Textualize/textual/issues/4403

## [0.56.2] - 2024-04-07

### Fixed

- Fixed inline mode not clearing with multiple screen

## [0.56.1] - 2024-04-07

### Fixed

- Fixed flicker when non-current screen updates https://github.com/Textualize/textual/pull/4401

### Changed

- Removed additional line at the end of an inline app https://github.com/Textualize/textual/pull/4401

## [0.56.0] - 2024-04-06

### Added

- Added `Size.with_width` and `Size.with_height` https://github.com/Textualize/textual/pull/4393

### Fixed

- Fixed issue with inline mode and multiple screens https://github.com/Textualize/textual/pull/4393
- Fixed issue with priority bindings https://github.com/Textualize/textual/pull/4395

### Changed

- self.prevent can be used in a widget constructor to prevent messages on mount https://github.com/Textualize/textual/pull/4392


## [0.55.1] - 2024-04-2

### Fixed

- Fixed mouse escape sequences being generated with `mouse=False`

## [0.55.0] - 2024-04-1

### Fixed

- Fix priority bindings not appearing in footer when key clashes with focused widget https://github.com/Textualize/textual/pull/4342
- Reverted auto-width change https://github.com/Textualize/textual/pull/4369

### Changed

- Exceptions inside `Widget.compose` or workers weren't bubbling up in tests https://github.com/Textualize/textual/issues/4282
- Fixed `DataTable` scrolling issues by changing `max-height` back to 100% https://github.com/Textualize/textual/issues/4286
- Fixed `Button` not rendering correctly with console markup https://github.com/Textualize/textual/issues/4328

### Added

- Added `Document.start` and `end` location properties for convenience https://github.com/Textualize/textual/pull/4267
- Added support for JavaScript, Golang, Rust, Bash, Java and Kotlin to `TextArea` https://github.com/Textualize/textual/pull/4350
- Added `inline` parameter to `run` and `run_async` to run app inline (under the prompt). https://github.com/Textualize/textual/pull/4343
- Added `mouse` parameter to disable mouse support https://github.com/Textualize/textual/pull/4343

## [0.54.0] - 2024-03-26

### Fixed

- Fixed a crash in `TextArea` when undoing an edit to a selection the selection was made backwards https://github.com/Textualize/textual/issues/4301
- Fixed issue with flickering scrollbars https://github.com/Textualize/textual/pull/4315
- Fixed issue where narrow TextArea would repeatedly wrap due to scrollbar appearing/disappearing https://github.com/Textualize/textual/pull/4334
- Fix progress bar ETA not updating when setting `total` reactive https://github.com/Textualize/textual/pull/4316

### Changed

- ProgressBar won't show ETA until there is at least one second of samples https://github.com/Textualize/textual/pull/4316
- `Input` waits until an edit has been made, after entry to the widget, before offering a suggestion https://github.com/Textualize/textual/pull/4335

## [0.53.1] - 2024-03-18

### Fixed

- Fixed issue with data binding https://github.com/Textualize/textual/pull/4308

## [0.53.0] - 2024-03-18

### Added

- Mapping of ANSI colors to hex codes configurable via `App.ansi_theme_dark` and `App.ansi_theme_light` https://github.com/Textualize/textual/pull/4192
- `Pilot.resize_terminal` to resize the terminal in testing https://github.com/Textualize/textual/issues/4212
- Added `sort_children` method https://github.com/Textualize/textual/pull/4244
- Support for pseudo-classes in nested TCSS https://github.com/Textualize/textual/issues/4039

### Fixed

- Fixed `TextArea.code_editor` missing recently added attributes https://github.com/Textualize/textual/pull/4172
- Fixed `Sparkline` not working with data in a `deque` https://github.com/Textualize/textual/issues/3899
- Tooltips are now cleared when the related widget is no longer under them https://github.com/Textualize/textual/issues/3045
- Simplified tree-sitter highlight queries for HTML, which also seems to fix segfault issue https://github.com/Textualize/textual/pull/4195
- Fixed `DirectoryTree.path` no longer reacting to new values https://github.com/Textualize/textual/issues/4208
- Fixed content size cache with Pretty widget https://github.com/Textualize/textual/pull/4211
- Fixed `grid-gutter` interaction with Pretty widget https://github.com/Textualize/textual/pull/4219
- Fixed `TextArea` styling issue on alternate screens https://github.com/Textualize/textual/pull/4220
- Fixed writing to invisible `RichLog` https://github.com/Textualize/textual/pull/4223
- Fixed `RichLog.min_width` not being used https://github.com/Textualize/textual/pull/4223
- Rename `CollapsibleTitle.action_toggle` to `action_toggle_collapsible` to fix clash with `DOMNode.action_toggle` https://github.com/Textualize/textual/pull/4221
- Markdown component classes weren't refreshed when watching for CSS https://github.com/Textualize/textual/issues/3464
- Rename `Switch.action_toggle` to `action_toggle_switch` to fix clash with `DOMNode.action_toggle` https://github.com/Textualize/textual/issues/4262
- Fixed `OptionList.OptionHighlighted` leaking out of `Select` https://github.com/Textualize/textual/issues/4224
- Fixed `Tab` enable/disable messages leaking into `TabbedContent` https://github.com/Textualize/textual/issues/4233
- Fixed a style leak from `TabbedContent` https://github.com/Textualize/textual/issues/4232
- Fixed active hidden scrollbars not releasing the mouse https://github.com/Textualize/textual/issues/4274
- Fixed the mouse not being released when hiding a `TextArea` while mouse selection is happening https://github.com/Textualize/textual/issues/4292
- Fix mouse scrolling not working when mouse cursor is over a disabled child widget https://github.com/Textualize/textual/issues/4242

### Changed

- Clicking a non focusable widget focus ancestors https://github.com/Textualize/textual/pull/4236
- BREAKING: widget class names must start with a capital letter or an underscore `_` https://github.com/Textualize/textual/pull/4252
- BREAKING: for many widgets, messages are now sent when programmatic changes that mirror user input are made https://github.com/Textualize/textual/pull/4256
  - Changed `Collapsible`
  - Changed `Markdown`
  - Changed `Select`
  - Changed `SelectionList`
  - Changed `TabbedContent`
  - Changed `Tabs`
  - Changed `TextArea`
  - Changed `Tree`
- Improved ETA calculation for ProgressBar https://github.com/Textualize/textual/pull/4271
- BREAKING: `AppFocus` and `AppBlur` are now posted when the terminal window gains or loses focus, if the terminal supports this https://github.com/Textualize/textual/pull/4265
  - When the terminal window loses focus, the currently-focused widget will also lose focus.
  - When the terminal window regains focus, the previously-focused widget will regain focus.
- TextArea binding for <kbd>ctrl</kbd>+<kbd>k</kbd> will now delete the line if the line is empty https://github.com/Textualize/textual/issues/4277
- The active tab (in `Tabs`) / tab pane (in `TabbedContent`) can now be unset https://github.com/Textualize/textual/issues/4241

## [0.52.1] - 2024-02-20

### Fixed

- Fixed the check for animation level in `LoadingIndicator` https://github.com/Textualize/textual/issues/4188

## [0.52.0] - 2024-02-19

### Changed

- Textual now writes to stderr rather than stdout https://github.com/Textualize/textual/pull/4177

### Added

- Added an `asyncio` lock attribute `Widget.lock` to be used to synchronize widget state https://github.com/Textualize/textual/issues/4134
- Added support for environment variable `TEXTUAL_ANIMATIONS` to control what animations Textual displays https://github.com/Textualize/textual/pull/4062
- Add attribute `App.animation_level` to control whether animations on that app run or not https://github.com/Textualize/textual/pull/4062
- Added support for a `TEXTUAL_SCREENSHOT_LOCATION` environment variable to specify the location of an automated screenshot https://github.com/Textualize/textual/pull/4181/
- Added support for a `TEXTUAL_SCREENSHOT_FILENAME` environment variable to specify the filename of an automated screenshot https://github.com/Textualize/textual/pull/4181/
- Added an `asyncio` lock attribute `Widget.lock` to be used to synchronize widget state https://github.com/Textualize/textual/issues/4134
- `Widget.remove_children` now accepts a CSS selector to specify which children to remove https://github.com/Textualize/textual/pull/4183
- `Widget.batch` combines widget locking and app update batching https://github.com/Textualize/textual/pull/4183

## [0.51.0] - 2024-02-15

### Added

- TextArea now has `read_only` mode https://github.com/Textualize/textual/pull/4151
- Add some syntax highlighting to TextArea default theme https://github.com/Textualize/textual/pull/4149
- Add undo and redo to TextArea https://github.com/Textualize/textual/pull/4124
- Added support for command palette command discoverability https://github.com/Textualize/textual/pull/4154

### Fixed

- Fixed out-of-view `Tab` not being scrolled into view when `Tabs.active` is assigned https://github.com/Textualize/textual/issues/4150
- Fixed `TabbedContent.TabActivate` not being posted when `TabbedContent.active` is assigned https://github.com/Textualize/textual/issues/4150

### Changed

- Breaking change: Renamed `TextArea.tab_behaviour` to `TextArea.tab_behavior` https://github.com/Textualize/textual/pull/4124
- `TextArea.theme` now defaults to `"css"` instead of None, and is no longer optional https://github.com/Textualize/textual/pull/4157

### Fixed

- Improve support for selector lists in nested TCSS https://github.com/Textualize/textual/issues/3969
- Improve support for rule declarations after nested TCSS rule sets https://github.com/Textualize/textual/issues/3999

## [0.50.1] - 2024-02-09

### Fixed

- Fixed tint applied to ANSI colors https://github.com/Textualize/textual/pull/4142

## [0.50.0] - 2024-02-08

### Fixed

- Fixed issue with ANSI colors not being converted to truecolor https://github.com/Textualize/textual/pull/4138
- Fixed duplicate watch methods being attached to DOM nodes https://github.com/Textualize/textual/pull/4030
- Fixed using `watch` to create additional watchers would trigger other watch methods https://github.com/Textualize/textual/issues/3878

### Added

- Added support for configuring dark and light themes for code in `Markdown` https://github.com/Textualize/textual/issues/3997

## [0.49.0] - 2024-02-07

### Fixed

- Fixed scrolling in long `OptionList` by adding max height of 100% https://github.com/Textualize/textual/issues/4021
- Fixed `DirectoryTree.clear_node` not clearing the node specified https://github.com/Textualize/textual/issues/4122

### Changed

- `DirectoryTree.reload` and `DirectoryTree.reload_node` now preserve state when reloading https://github.com/Textualize/textual/issues/4056
- Fixed a crash in the TextArea when performing a backward replace https://github.com/Textualize/textual/pull/4126
- Fixed selection not updating correctly when pasting while there's a non-zero selection https://github.com/Textualize/textual/pull/4126
- Breaking change: `TextArea` will not use `Escape` to shift focus if the `tab_behaviour` is the default https://github.com/Textualize/textual/issues/4110
- `TextArea` cursor will now be invisible before first focus https://github.com/Textualize/textual/pull/4128
- Fix toggling `TextArea.cursor_blink` reactive when widget does not have focus https://github.com/Textualize/textual/pull/4128

### Added

- Added DOMQuery.set https://github.com/Textualize/textual/pull/4075
- Added DOMNode.set_reactive https://github.com/Textualize/textual/pull/4075
- Added DOMNode.data_bind https://github.com/Textualize/textual/pull/4075
- Added DOMNode.action_toggle https://github.com/Textualize/textual/pull/4075
- Added Worker.cancelled_event https://github.com/Textualize/textual/pull/4075
- `Tree` (and `DirectoryTree`) grew an attribute `lock` that can be used for synchronization across coroutines https://github.com/Textualize/textual/issues/4056


## [0.48.2] - 2024-02-02

### Fixed

- Fixed a hang in the Linux driver when connected to a pipe https://github.com/Textualize/textual/issues/4104
- Fixed broken `OptionList` `Option.id` mappings https://github.com/Textualize/textual/issues/4101

### Changed

- Breaking change: keyboard navigation in `RadioSet`, `ListView`, `OptionList`, and `SelectionList`, no longer allows highlighting disabled items https://github.com/Textualize/textual/issues/3881

## [0.48.1] - 2024-02-01

### Fixed

- `TextArea` uses CSS theme by default instead of `monokai` https://github.com/Textualize/textual/pull/4091

## [0.48.0] - 2024-02-01

### Changed

- Breaking change: Significant changes to `TextArea.__init__` default values/behaviour https://github.com/Textualize/textual/pull/3933
  - `soft_wrap=True` - soft wrapping is now enabled by default.
  - `show_line_numbers=False` - line numbers are now disabled by default.
  - `tab_behaviour="focus"` - pressing the tab key now switches focus instead of indenting by default.
- Breaking change: `TextArea` default theme changed to CSS, and default styling changed https://github.com/Textualize/textual/pull/4074
- Breaking change: `DOMNode.has_pseudo_class` now accepts a single name only https://github.com/Textualize/textual/pull/3970
- Made `textual.cache` (formerly `textual._cache`) public https://github.com/Textualize/textual/pull/3976
- `Tab.label` can now be used to change the label of a tab https://github.com/Textualize/textual/pull/3979
- Changed the default notification timeout from 3 to 5 seconds https://github.com/Textualize/textual/pull/4059
- Prior scroll animations are now cancelled on new scrolls https://github.com/Textualize/textual/pull/4081

### Added

- Added `DOMNode.has_pseudo_classes` https://github.com/Textualize/textual/pull/3970
- Added `Widget.allow_focus` and `Widget.allow_focus_children` https://github.com/Textualize/textual/pull/3989
- Added `TextArea.soft_wrap` reactive attribute added https://github.com/Textualize/textual/pull/3933
- Added `TextArea.tab_behaviour` reactive attribute added https://github.com/Textualize/textual/pull/3933
- Added `TextArea.code_editor` classmethod/alternative constructor https://github.com/Textualize/textual/pull/3933
- Added `TextArea.wrapped_document` attribute which can convert between wrapped visual coordinates and locations https://github.com/Textualize/textual/pull/3933
- Added `show_line_numbers` to `TextArea.__init__` https://github.com/Textualize/textual/pull/3933
- Added component classes allowing `TextArea` to be styled using CSS https://github.com/Textualize/textual/pull/4074
- Added `Query.blur` and `Query.focus` https://github.com/Textualize/textual/pull/4012
- Added `MessagePump.message_queue_size` https://github.com/Textualize/textual/pull/4012
- Added `TabbedContent.active_pane` https://github.com/Textualize/textual/pull/4012
- Added `App.suspend` https://github.com/Textualize/textual/pull/4064
- Added `App.action_suspend_process` https://github.com/Textualize/textual/pull/4064


### Fixed

- Parameter `animate` from `DataTable.move_cursor` was being ignored https://github.com/Textualize/textual/issues/3840
- Fixed a crash if `DirectoryTree.show_root` was set before the DOM was fully available https://github.com/Textualize/textual/issues/2363
- Live reloading of TCSS wouldn't apply CSS changes to screens under the top screen of the stack https://github.com/Textualize/textual/issues/3931
- `SelectionList` option IDs are usable as soon as the widget is instantiated https://github.com/Textualize/textual/issues/3903
- Fix issue with `Strip.crop` when crop window start aligned with strip end https://github.com/Textualize/textual/pull/3998
- Fixed Strip.crop_extend https://github.com/Textualize/textual/pull/4011
- Fix for percentage dimensions https://github.com/Textualize/textual/pull/4037
- Fixed a crash if the `TextArea` language was set but tree-sitter language binaries were not installed https://github.com/Textualize/textual/issues/4045
- Ensuring `TextArea.SelectionChanged` message only sends when the updated selection is different https://github.com/Textualize/textual/pull/3933
- Fixed declaration after nested rule set causing a parse error https://github.com/Textualize/textual/pull/4012
- ID and class validation was too lenient https://github.com/Textualize/textual/issues/3954
- Fixed CSS watcher crash if file becomes unreadable (even temporarily) https://github.com/Textualize/textual/pull/4079
- Fixed display of keys when used in conjunction with other keys https://github.com/Textualize/textual/pull/3050
- Fixed double detection of <kbd>Escape</kbd> on Windows https://github.com/Textualize/textual/issues/4038


## [0.47.1] - 2024-01-05

### Fixed

- Fixed nested specificity https://github.com/Textualize/textual/pull/3963

## [0.47.0] - 2024-01-04

### Fixed

- `Widget.move_child` would break if `before`/`after` is set to the index of the widget in `child` https://github.com/Textualize/textual/issues/1743
- Fixed auto width text not processing markup https://github.com/Textualize/textual/issues/3918
- Fixed `Tree.clear` not retaining the root's expanded state https://github.com/Textualize/textual/issues/3557

### Changed

- Breaking change: `Widget.move_child` parameters `before` and `after` are now keyword-only https://github.com/Textualize/textual/pull/3896
- Style tweak to toasts https://github.com/Textualize/textual/pull/3955

### Added

- Added textual.lazy https://github.com/Textualize/textual/pull/3936
- Added App.push_screen_wait https://github.com/Textualize/textual/pull/3955
- Added nesting of CSS https://github.com/Textualize/textual/pull/3946

## [0.46.0] - 2023-12-17

### Fixed

- Disabled radio buttons could be selected with the keyboard https://github.com/Textualize/textual/issues/3839
- Fixed zero width scrollbars causing content to disappear https://github.com/Textualize/textual/issues/3886

### Changed

- The tabs within a `TabbedContent` now prefix their IDs to stop any clash with their associated `TabPane` https://github.com/Textualize/textual/pull/3815
- Breaking change: `tab` is no longer a `@on` decorator selector for `TabbedContent.TabActivated` -- use `pane` instead https://github.com/Textualize/textual/pull/3815

### Added

- Added `Collapsible.title` reactive attribute https://github.com/Textualize/textual/pull/3830
- Added a `pane` attribute to `TabbedContent.TabActivated` https://github.com/Textualize/textual/pull/3815
- Added caching of rules attributes and `cache` parameter to Stylesheet.apply https://github.com/Textualize/textual/pull/3880

## [0.45.1] - 2023-12-12

### Fixed

- Fixed issues where styles wouldn't update if changed in mount. https://github.com/Textualize/textual/pull/3860

## [0.45.0] - 2023-12-12

### Fixed

- Fixed `DataTable.update_cell` not raising an error with an invalid column key https://github.com/Textualize/textual/issues/3335
- Fixed `Input` showing suggestions when not focused https://github.com/Textualize/textual/pull/3808
- Fixed loading indicator not covering scrollbars https://github.com/Textualize/textual/pull/3816

### Removed

- Removed renderables/align.py which was no longer used.

### Changed

- Dropped ALLOW_CHILDREN flag introduced in 0.43.0 https://github.com/Textualize/textual/pull/3814
- Widgets with an auto height in an auto height container will now expand if they have no siblings https://github.com/Textualize/textual/pull/3814
- Breaking change: Removed `limit_rules` from Stylesheet.apply https://github.com/Textualize/textual/pull/3844

### Added

- Added `get_loading_widget` to Widget and App customize the loading widget. https://github.com/Textualize/textual/pull/3816
- Added messages `Collapsible.Expanded` and `Collapsible.Collapsed` that inherit from `Collapsible.Toggled`. https://github.com/Textualize/textual/issues/3824

## [0.44.1] - 2023-12-4

### Fixed

- Fixed slow scrolling when there are many widgets https://github.com/Textualize/textual/pull/3801

## [0.44.0] - 2023-12-1

### Changed

- Breaking change: Dropped 3.7 support https://github.com/Textualize/textual/pull/3766
- Breaking changes https://github.com/Textualize/textual/issues/1530
 - `link-hover-background` renamed to `link-background-hover`
 - `link-hover-color` renamed to `link-color-hover`
 - `link-hover-style` renamed to `link-style-hover`
- `Tree` now forces a scroll when `scroll_to_node` is called https://github.com/Textualize/textual/pull/3786
- Brought rxvt's use of shift-numpad keys in line with most other terminals https://github.com/Textualize/textual/pull/3769

### Added

- Added support for Ctrl+Fn and Ctrl+Shift+Fn keys in urxvt https://github.com/Textualize/textual/pull/3737
- Friendly error messages when trying to mount non-widgets https://github.com/Textualize/textual/pull/3780
- Added `Select.from_values` class method that can be used to initialize a Select control with an iterator of values https://github.com/Textualize/textual/pull/3743

### Fixed

- Fixed NoWidget when mouse goes outside window https://github.com/Textualize/textual/pull/3790
- Removed spurious print statements from press_keys https://github.com/Textualize/textual/issues/3785

## [0.43.2] - 2023-11-29

### Fixed

- Fixed NoWidget error https://github.com/Textualize/textual/pull/3779

## [0.43.1] - 2023-11-29

### Fixed

- Fixed clicking on scrollbar moves TextArea cursor https://github.com/Textualize/textual/issues/3763

## [0.43.0] - 2023-11-28

### Fixed

- Fixed mouse targeting issue in `TextArea` when tabs were not fully expanded https://github.com/Textualize/textual/pull/3725
- Fixed `Select` not updating after changing the `prompt` reactive https://github.com/Textualize/textual/issues/2983
- Fixed flicker when updating Markdown https://github.com/Textualize/textual/pull/3757

### Added

- Added experimental Canvas class https://github.com/Textualize/textual/pull/3669/
- Added `keyline` rule https://github.com/Textualize/textual/pull/3669/
- Widgets can now have an ALLOW_CHILDREN (bool) classvar to disallow adding children to a widget https://github.com/Textualize/textual/pull/3758
- Added the ability to set the `label` property of a `Checkbox` https://github.com/Textualize/textual/pull/3765
- Added the ability to set the `label` property of a `RadioButton` https://github.com/Textualize/textual/pull/3765
- Added support for various modified edit and navigation keys in urxvt https://github.com/Textualize/textual/pull/3739
- Added app focus/blur for textual-web https://github.com/Textualize/textual/pull/3767

### Changed

- Method `MarkdownTableOfContents.set_table_of_contents` renamed to `MarkdownTableOfContents.rebuild_table_of_contents` https://github.com/Textualize/textual/pull/3730
- Exception `Tree.UnknownNodeID` moved out of `Tree`, import from `textual.widgets.tree` https://github.com/Textualize/textual/pull/3730
- Exception `TreeNode.RemoveRootError` moved out of `TreeNode`, import from `textual.widgets.tree` https://github.com/Textualize/textual/pull/3730
- Optimized startup time https://github.com/Textualize/textual/pull/3753
- App.COMMANDS or Screen.COMMANDS can now accept a callable which returns a command palette provider https://github.com/Textualize/textual/pull/3756

## [0.42.0] - 2023-11-22

### Fixed

- Duplicate CSS errors when parsing CSS from a screen https://github.com/Textualize/textual/issues/3581
- Added missing `blur` pseudo class https://github.com/Textualize/textual/issues/3439
- Fixed visual glitched characters on Windows due to Python limitation https://github.com/Textualize/textual/issues/2548
- Fixed `ScrollableContainer` to receive focus https://github.com/Textualize/textual/pull/3632
- Fixed app-level queries causing a crash when the command palette is active https://github.com/Textualize/textual/issues/3633
- Fixed outline not rendering correctly in some scenarios (e.g. on Button widgets) https://github.com/Textualize/textual/issues/3628
- Fixed live-reloading of screen CSS https://github.com/Textualize/textual/issues/3454
- `Select.value` could be in an invalid state https://github.com/Textualize/textual/issues/3612
- Off-by-one in CSS error reporting https://github.com/Textualize/textual/issues/3625
- Loading indicators and app notifications overlapped in the wrong order https://github.com/Textualize/textual/issues/3677
- Widgets being loaded are disabled and have their scrolling explicitly disabled too https://github.com/Textualize/textual/issues/3677
- Method render on a widget could be called before mounting said widget https://github.com/Textualize/textual/issues/2914

### Added

- Exceptions to `textual.widgets.select` https://github.com/Textualize/textual/pull/3614
  - `InvalidSelectValueError` for when setting a `Select` to an invalid value
  - `EmptySelectError` when creating/setting a `Select` to have no options when `allow_blank` is `False`
- `Select` methods https://github.com/Textualize/textual/pull/3614
  - `clear`
  - `is_blank`
- Constant `Select.BLANK` to flag an empty selection https://github.com/Textualize/textual/pull/3614
- Added `restrict`, `type`, `max_length`, and `valid_empty` to Input https://github.com/Textualize/textual/pull/3657
- Added `Pilot.mouse_down` to simulate `MouseDown` events https://github.com/Textualize/textual/pull/3495
- Added `Pilot.mouse_up` to simulate `MouseUp` events https://github.com/Textualize/textual/pull/3495
- Added `Widget.is_mounted` property https://github.com/Textualize/textual/pull/3709
- Added `TreeNode.refresh` https://github.com/Textualize/textual/pull/3639

### Changed

- CSS error reporting will no longer provide links to the files in question https://github.com/Textualize/textual/pull/3582
- inline CSS error reporting will report widget/class variable where the CSS was read from https://github.com/Textualize/textual/pull/3582
- Breaking change: `Tree.refresh_line` has now become an internal https://github.com/Textualize/textual/pull/3639
- Breaking change: Setting `Select.value` to `None` no longer clears the selection (See `Select.BLANK` and `Select.clear`) https://github.com/Textualize/textual/pull/3614
- Breaking change: `Button` no longer inherits from `Static`, now it inherits directly from `Widget` https://github.com/Textualize/textual/issues/3603
- Rich markup in markdown headings is now escaped when building the TOC https://github.com/Textualize/textual/issues/3689
- Mechanics behind mouse clicks. See [this](https://github.com/Textualize/textual/pull/3495#issue-1934915047) for more details. https://github.com/Textualize/textual/pull/3495
- Breaking change: max/min-width/height now includes padding and border. https://github.com/Textualize/textual/pull/3712

## [0.41.0] - 2023-10-31

### Fixed

- Fixed `Input.cursor_blink` reactive not changing blink state after `Input` was mounted https://github.com/Textualize/textual/pull/3498
- Fixed `Tabs.active` attribute value not being re-assigned after removing a tab or clearing https://github.com/Textualize/textual/pull/3498
- Fixed `DirectoryTree` race-condition crash when changing path https://github.com/Textualize/textual/pull/3498
- Fixed issue with `LRUCache.discard` https://github.com/Textualize/textual/issues/3537
- Fixed `DataTable` not scrolling to rows that were just added https://github.com/Textualize/textual/pull/3552
- Fixed cache bug with `DataTable.update_cell` https://github.com/Textualize/textual/pull/3551
- Fixed CSS errors being repeated https://github.com/Textualize/textual/pull/3566
- Fix issue with chunky highlights on buttons https://github.com/Textualize/textual/pull/3571
- Fixed `OptionList` event leakage from `CommandPalette` to `App`.
- Fixed crash in `LoadingIndicator` https://github.com/Textualize/textual/pull/3498
- Fixed crash when `Tabs` appeared as a descendant of `TabbedContent` in the DOM https://github.com/Textualize/textual/pull/3602
- Fixed the command palette cancelling other workers https://github.com/Textualize/textual/issues/3615

### Added

- Add Document `get_index_from_location` / `get_location_from_index` https://github.com/Textualize/textual/pull/3410
- Add setter for `TextArea.text` https://github.com/Textualize/textual/discussions/3525
- Added `key` argument to the `DataTable.sort()` method, allowing the table to be sorted using a custom function (or other callable) https://github.com/Textualize/textual/pull/3090
- Added `initial` to all css rules, which restores default (i.e. value from DEFAULT_CSS) https://github.com/Textualize/textual/pull/3566
- Added HorizontalPad to pad.py https://github.com/Textualize/textual/pull/3571
- Added `AwaitComplete` class, to be used for optionally awaitable return values https://github.com/Textualize/textual/pull/3498

### Changed

- Breaking change: `Button.ACTIVE_EFFECT_DURATION` classvar converted to `Button.active_effect_duration` attribute https://github.com/Textualize/textual/pull/3498
- Breaking change: `Input.blink_timer` made private (renamed to `Input._blink_timer`) https://github.com/Textualize/textual/pull/3498
- Breaking change: `Input.cursor_blink` reactive updated to not run on mount (now `init=False`) https://github.com/Textualize/textual/pull/3498
- Breaking change: `AwaitTabbedContent` class removed https://github.com/Textualize/textual/pull/3498
- Breaking change: `Tabs.remove_tab` now returns an `AwaitComplete` instead of an `AwaitRemove` https://github.com/Textualize/textual/pull/3498
- Breaking change: `Tabs.clear` now returns an `AwaitComplete` instead of an `AwaitRemove` https://github.com/Textualize/textual/pull/3498
- `TabbedContent.add_pane` now returns an `AwaitComplete` instead of an `AwaitTabbedContent` https://github.com/Textualize/textual/pull/3498
- `TabbedContent.remove_pane` now returns an `AwaitComplete` instead of an `AwaitTabbedContent` https://github.com/Textualize/textual/pull/3498
- `TabbedContent.clear_pane` now returns an `AwaitComplete` instead of an `AwaitTabbedContent` https://github.com/Textualize/textual/pull/3498
- `Tabs.add_tab` now returns an `AwaitComplete` instead of an `AwaitMount` https://github.com/Textualize/textual/pull/3498
- `DirectoryTree.reload` now returns an `AwaitComplete`, which may be awaited to ensure the node has finished being processed by the internal queue https://github.com/Textualize/textual/pull/3498
- `Tabs.remove_tab` now returns an `AwaitComplete`, which may be awaited to ensure the tab is unmounted and internal state is updated https://github.com/Textualize/textual/pull/3498
- `App.switch_mode` now returns an `AwaitMount`, which may be awaited to ensure the screen is mounted https://github.com/Textualize/textual/pull/3498
- Buttons will now display multiple lines, and have auto height https://github.com/Textualize/textual/pull/3539
- DataTable now has a max-height of 100vh rather than 100%, which doesn't work with auto
- Breaking change: empty rules now result in an error https://github.com/Textualize/textual/pull/3566
- Improved startup time by caching CSS parsing https://github.com/Textualize/textual/pull/3575
- Workers are now created/run in a thread-safe way https://github.com/Textualize/textual/pull/3586

## [0.40.0] - 2023-10-11

### Added

- Added `loading` reactive property to widgets https://github.com/Textualize/textual/pull/3509

## [0.39.0] - 2023-10-10

### Fixed

- `Pilot.click`/`Pilot.hover` can't use `Screen` as a selector https://github.com/Textualize/textual/issues/3395
- App exception when a `Tree` is initialized/mounted with `disabled=True` https://github.com/Textualize/textual/issues/3407
- Fixed `print` locations not being correctly reported in `textual console` https://github.com/Textualize/textual/issues/3237
- Fix location of IME and emoji popups https://github.com/Textualize/textual/pull/3408
- Fixed application freeze when pasting an emoji into an application on Windows https://github.com/Textualize/textual/issues/3178
- Fixed duplicate option ID handling in the `OptionList` https://github.com/Textualize/textual/issues/3455
- Fix crash when removing and updating DataTable cell at same time https://github.com/Textualize/textual/pull/3487
- Fixed fractional styles to allow integer values https://github.com/Textualize/textual/issues/3414
- Stop eating stdout/stderr in headless mode - print works again in tests https://github.com/Textualize/textual/pull/3486

### Added

- `OutOfBounds` exception to be raised by `Pilot` https://github.com/Textualize/textual/pull/3360
- `TextArea.cursor_screen_offset` property for getting the screen-relative position of the cursor https://github.com/Textualize/textual/pull/3408
- `Input.cursor_screen_offset` property for getting the screen-relative position of the cursor https://github.com/Textualize/textual/pull/3408
- Reactive `cell_padding` (and respective parameter) to define horizontal cell padding in data table columns https://github.com/Textualize/textual/issues/3435
- Added `Input.clear` method https://github.com/Textualize/textual/pull/3430
- Added `TextArea.SelectionChanged` and `TextArea.Changed` messages https://github.com/Textualize/textual/pull/3442
- Added `wait_for_dismiss` parameter to `App.push_screen` https://github.com/Textualize/textual/pull/3477
- Allow scrollbar-size to be set to 0 to achieve scrollable containers with no visible scrollbars https://github.com/Textualize/textual/pull/3488

### Changed

- Breaking change: tree-sitter and tree-sitter-languages dependencies moved to `syntax` extra https://github.com/Textualize/textual/pull/3398
- `Pilot.click`/`Pilot.hover` now raises `OutOfBounds` when clicking outside visible screen https://github.com/Textualize/textual/pull/3360
- `Pilot.click`/`Pilot.hover` now return a Boolean indicating whether the click/hover landed on the widget that matches the selector https://github.com/Textualize/textual/pull/3360
- Added a delay to when the `No Matches` message appears in the command palette, thus removing a flicker https://github.com/Textualize/textual/pull/3399
- Timer callbacks are now typed more loosely https://github.com/Textualize/textual/issues/3434

## [0.38.1] - 2023-09-21

### Fixed

- Hotfix - added missing highlight files in build distribution https://github.com/Textualize/textual/pull/3370

## [0.38.0] - 2023-09-21

### Added

- Added a TextArea https://github.com/Textualize/textual/pull/2931
- Added :dark and :light pseudo classes

### Fixed

- Fixed `DataTable` not updating component styles on hot-reloading https://github.com/Textualize/textual/issues/3312

### Changed

- Breaking change: CSS in DEFAULT_CSS is now automatically scoped to the widget (set SCOPED_CSS=False) to disable
- Breaking change: Changed `Markdown.goto_anchor` to return a boolean (if the anchor was found) instead of `None` https://github.com/Textualize/textual/pull/3334

## [0.37.1] - 2023-09-16

### Fixed

- Fixed the command palette crashing with a `TimeoutError` in any Python before 3.11 https://github.com/Textualize/textual/issues/3320
- Fixed `Input` event leakage from `CommandPalette` to `App`.

## [0.37.0] - 2023-09-15

### Added

- Added the command palette https://github.com/Textualize/textual/pull/3058
- `Input` is now validated when focus moves out of it https://github.com/Textualize/textual/pull/3193
- Attribute `Input.validate_on` (and `__init__` parameter of the same name) to customise when validation occurs https://github.com/Textualize/textual/pull/3193
- Screen-specific (sub-)title attributes https://github.com/Textualize/textual/pull/3199:
  - `Screen.TITLE`
  - `Screen.SUB_TITLE`
  - `Screen.title`
  - `Screen.sub_title`
- Properties `Header.screen_title` and `Header.screen_sub_title` https://github.com/Textualize/textual/pull/3199
- Added `DirectoryTree.DirectorySelected` message https://github.com/Textualize/textual/issues/3200
- Added `widgets.Collapsible` contributed by Sunyoung Yoo https://github.com/Textualize/textual/pull/2989

### Fixed

- Fixed a crash when removing an option from an `OptionList` while the mouse is hovering over the last option https://github.com/Textualize/textual/issues/3270
- Fixed a crash in `MarkdownViewer` when clicking on a link that contains an anchor https://github.com/Textualize/textual/issues/3094
- Fixed wrong message pump in pop_screen https://github.com/Textualize/textual/pull/3315

### Changed

- Widget.notify and App.notify are now thread-safe https://github.com/Textualize/textual/pull/3275
- Breaking change: Widget.notify and App.notify now return None https://github.com/Textualize/textual/pull/3275
- App.unnotify is now private (renamed to App._unnotify) https://github.com/Textualize/textual/pull/3275
- `Markdown.load` will now attempt to scroll to a related heading if an anchor is provided https://github.com/Textualize/textual/pull/3244
- `ProgressBar` explicitly supports being set back to its indeterminate state https://github.com/Textualize/textual/pull/3286

## [0.36.0] - 2023-09-05

### Added

- TCSS styles `layer` and `layers` can be strings https://github.com/Textualize/textual/pull/3169
- `App.return_code` for the app return code https://github.com/Textualize/textual/pull/3202
- Added `animate` switch to `Tree.scroll_to_line` and `Tree.scroll_to_node` https://github.com/Textualize/textual/pull/3210
- Added `Rule` widget https://github.com/Textualize/textual/pull/3209
- Added App.current_mode to get the current mode https://github.com/Textualize/textual/pull/3233

### Changed

- Reactive callbacks are now scheduled on the message pump of the reactable that is watching instead of the owner of reactive attribute https://github.com/Textualize/textual/pull/3065
- Callbacks scheduled with `call_next` will now have the same prevented messages as when the callback was scheduled https://github.com/Textualize/textual/pull/3065
- Added `cursor_type` to the `DataTable` constructor.
- Fixed `push_screen` not updating Screen.CSS styles https://github.com/Textualize/textual/issues/3217
- `DataTable.add_row` accepts `height=None` to automatically compute optimal height for a row https://github.com/Textualize/textual/pull/3213

### Fixed

- Fixed flicker when calling pop_screen multiple times https://github.com/Textualize/textual/issues/3126
- Fixed setting styles.layout not updating https://github.com/Textualize/textual/issues/3047
- Fixed flicker when scrolling tree up or down a line https://github.com/Textualize/textual/issues/3206

## [0.35.1]

### Fixed

- Fixed flash of 80x24 interface in textual-web

## [0.35.0]

### Added

- Ability to enable/disable tabs via the reactive `disabled` in tab panes https://github.com/Textualize/textual/pull/3152
- Textual-web driver support for Windows

### Fixed

- Could not hide/show/disable/enable tabs in nested `TabbedContent` https://github.com/Textualize/textual/pull/3150

## [0.34.0] - 2023-08-22

### Added

- Methods `TabbedContent.disable_tab` and `TabbedContent.enable_tab` https://github.com/Textualize/textual/pull/3112
- Methods `Tabs.disable` and `Tabs.enable` https://github.com/Textualize/textual/pull/3112
- Messages `Tab.Disabled`, `Tab.Enabled`, `Tabs.TabDisabled` and `Tabs.Enabled` https://github.com/Textualize/textual/pull/3112
- Methods `TabbedContent.hide_tab` and `TabbedContent.show_tab` https://github.com/Textualize/textual/pull/3112
- Methods `Tabs.hide` and `Tabs.show` https://github.com/Textualize/textual/pull/3112
- Messages `Tabs.TabHidden` and `Tabs.TabShown` https://github.com/Textualize/textual/pull/3112
- Added `ListView.extend` method to append multiple items https://github.com/Textualize/textual/pull/3012

### Changed

- grid-columns and grid-rows now accept an `auto` token to detect the optimal size https://github.com/Textualize/textual/pull/3107
- LoadingIndicator now has a minimum height of 1 line.

### Fixed

- Fixed auto height container with default grid-rows https://github.com/Textualize/textual/issues/1597
- Fixed `page_up` and `page_down` bug in `DataTable` when `show_header = False` https://github.com/Textualize/textual/pull/3093
- Fixed issue with visible children inside invisible container when moving focus https://github.com/Textualize/textual/issues/3053

## [0.33.0] - 2023-08-15

### Fixed

- Fixed unintuitive sizing behaviour of TabbedContent https://github.com/Textualize/textual/issues/2411
- Fixed relative units not always expanding auto containers https://github.com/Textualize/textual/pull/3059
- Fixed background refresh https://github.com/Textualize/textual/issues/3055
- Fixed `SelectionList.clear_options` https://github.com/Textualize/textual/pull/3075
- `MouseMove` events bubble up from widgets. `App` and `Screen` receive `MouseMove` events even if there's no Widget under the cursor. https://github.com/Textualize/textual/issues/2905
- Fixed click on double-width char https://github.com/Textualize/textual/issues/2968

### Changed

- Breaking change: `DOMNode.visible` now takes into account full DOM to report whether a node is visible or not.

### Removed

- Property `Widget.focusable_children` https://github.com/Textualize/textual/pull/3070

### Added

- Added an interface for replacing prompt of an individual option in an `OptionList` https://github.com/Textualize/textual/issues/2603
- Added `DirectoryTree.reload_node` method https://github.com/Textualize/textual/issues/2757
- Added widgets.Digit https://github.com/Textualize/textual/pull/3073
- Added `BORDER_TITLE` and `BORDER_SUBTITLE` classvars to Widget https://github.com/Textualize/textual/pull/3097

### Changed

- DescendantBlur and DescendantFocus can now be used with @on decorator

## [0.32.0] - 2023-08-03

### Added

- Added widgets.Log
- Added Widget.is_vertical_scroll_end, Widget.is_horizontal_scroll_end, Widget.is_vertical_scrollbar_grabbed, Widget.is_horizontal_scrollbar_grabbed

### Changed

- Breaking change: Renamed TextLog to RichLog

## [0.31.0] - 2023-08-01

### Added

- Added App.begin_capture_print, App.end_capture_print, Widget.begin_capture_print, Widget.end_capture_print https://github.com/Textualize/textual/issues/2952
- Added the ability to run async methods as thread workers https://github.com/Textualize/textual/pull/2938
- Added `App.stop_animation` https://github.com/Textualize/textual/issues/2786
- Added `Widget.stop_animation` https://github.com/Textualize/textual/issues/2786

### Changed

- Breaking change: Creating a thread worker now requires that a `thread=True` keyword argument is passed https://github.com/Textualize/textual/pull/2938
- Breaking change: `Markdown.load` no longer captures all errors and returns a `bool`, errors now propagate https://github.com/Textualize/textual/issues/2956
- Breaking change: the default style of a `DataTable` now has `max-height: 100%` https://github.com/Textualize/textual/issues/2959

### Fixed

- Fixed a crash when a `SelectionList` had a prompt wider than itself https://github.com/Textualize/textual/issues/2900
- Fixed a bug where `Click` events were bubbling up from `Switch` widgets https://github.com/Textualize/textual/issues/2366
- Fixed a crash when using empty CSS variables https://github.com/Textualize/textual/issues/1849
- Fixed issue with tabs in TextLog https://github.com/Textualize/textual/issues/3007
- Fixed a bug with `DataTable` hover highlighting https://github.com/Textualize/textual/issues/2909

## [0.30.0] - 2023-07-17

### Added

- Added `DataTable.remove_column` method https://github.com/Textualize/textual/pull/2899
- Added notifications https://github.com/Textualize/textual/pull/2866
- Added `on_complete` callback to scroll methods https://github.com/Textualize/textual/pull/2903

### Fixed

- Fixed CancelledError issue with timer https://github.com/Textualize/textual/issues/2854
- Fixed Toggle Buttons issue with not being clickable/hoverable https://github.com/Textualize/textual/pull/2930


## [0.29.0] - 2023-07-03

### Changed

- Factored dev tools (`textual` command) in to external lib (`textual-dev`).

### Added

- Updated `DataTable.get_cell` type hints to accept string keys https://github.com/Textualize/textual/issues/2586
- Added `DataTable.get_cell_coordinate` method
- Added `DataTable.get_row_index` method https://github.com/Textualize/textual/issues/2587
- Added `DataTable.get_column_index` method
- Added can-focus pseudo-class to target widgets that may receive focus
- Make `Markdown.update` optionally awaitable https://github.com/Textualize/textual/pull/2838
- Added `default` parameter to `DataTable.add_column` for populating existing rows https://github.com/Textualize/textual/pull/2836
- Added can-focus pseudo-class to target widgets that may receive focus

### Fixed

- Fixed crash when columns were added to populated `DataTable` https://github.com/Textualize/textual/pull/2836
- Fixed issues with opacity on Screens https://github.com/Textualize/textual/issues/2616
- Fixed style problem with selected selections in a non-focused selection list https://github.com/Textualize/textual/issues/2768
- Fixed sys.stdout and sys.stderr being None https://github.com/Textualize/textual/issues/2879

## [0.28.1] - 2023-06-20

### Fixed

- Fixed indented code blocks not showing up in `Markdown` https://github.com/Textualize/textual/issues/2781
- Fixed inline code blocks in lists showing out of order in `Markdown` https://github.com/Textualize/textual/issues/2676
- Fixed list items in a `Markdown` being added to the focus chain https://github.com/Textualize/textual/issues/2380
- Fixed `Tabs` posting unnecessary messages when removing non-active tabs https://github.com/Textualize/textual/issues/2807
- call_after_refresh will preserve the sender within the callback https://github.com/Textualize/textual/pull/2806

### Added

- Added a method of allowing third party code to handle unhandled tokens in `Markdown` https://github.com/Textualize/textual/pull/2803
- Added `MarkdownBlock` as an exported symbol in `textual.widgets.markdown` https://github.com/Textualize/textual/pull/2803

### Changed

- Tooltips are now inherited, so will work with compound widgets


## [0.28.0] - 2023-06-19

### Added

- The devtools console now confirms when CSS files have been successfully loaded after a previous error https://github.com/Textualize/textual/pull/2716
- Class variable `CSS` to screens https://github.com/Textualize/textual/issues/2137
- Class variable `CSS_PATH` to screens https://github.com/Textualize/textual/issues/2137
- Added `cursor_foreground_priority` and `cursor_background_priority` to `DataTable` https://github.com/Textualize/textual/pull/2736
- Added Region.center
- Added `center` parameter to `Widget.scroll_to_region`
- Added `origin_visible` parameter to `Widget.scroll_to_region`
- Added `origin_visible` parameter to `Widget.scroll_to_center`
- Added `TabbedContent.tab_count` https://github.com/Textualize/textual/pull/2751
- Added `TabbedContent.add_pane` https://github.com/Textualize/textual/pull/2751
- Added `TabbedContent.remove_pane` https://github.com/Textualize/textual/pull/2751
- Added `TabbedContent.clear_panes` https://github.com/Textualize/textual/pull/2751
- Added `TabbedContent.Cleared` https://github.com/Textualize/textual/pull/2751

### Fixed

- Fixed setting `TreeNode.label` on an existing `Tree` node not immediately refreshing https://github.com/Textualize/textual/pull/2713
- Correctly implement `__eq__` protocol in DataTable https://github.com/Textualize/textual/pull/2705
- Fixed exceptions in Pilot tests being silently ignored https://github.com/Textualize/textual/pull/2754
- Fixed issue where internal data of `OptionList` could be invalid for short window after `clear_options` https://github.com/Textualize/textual/pull/2754
- Fixed `Tooltip` causing a `query_one` on a lone `Static` to fail https://github.com/Textualize/textual/issues/2723
- Nested widgets wouldn't lose focus when parent is disabled https://github.com/Textualize/textual/issues/2772
- Fixed the `Tabs` `Underline` highlight getting "lost" in some extreme situations https://github.com/Textualize/textual/pull/2751

### Changed

- Breaking change: The `@on` decorator will now match a message class and any child classes https://github.com/Textualize/textual/pull/2746
- Breaking change: Styles update to checkbox, radiobutton, OptionList, Select, SelectionList, Switch https://github.com/Textualize/textual/pull/2777
- `Tabs.add_tab` is now optionally awaitable https://github.com/Textualize/textual/pull/2778
- `Tabs.add_tab` now takes `before` and `after` arguments to position a new tab https://github.com/Textualize/textual/pull/2778
- `Tabs.remove_tab` is now optionally awaitable https://github.com/Textualize/textual/pull/2778
- Breaking change: `Tabs.clear` has been changed from returning `self` to being optionally awaitable https://github.com/Textualize/textual/pull/2778

## [0.27.0] - 2023-06-01

### Fixed

- Fixed zero division error https://github.com/Textualize/textual/issues/2673
- Fix `scroll_to_center` when there were nested layers out of view (Compositor full_map not populated fully) https://github.com/Textualize/textual/pull/2684
- Fix crash when `Select` widget value attribute was set in `compose` https://github.com/Textualize/textual/pull/2690
- Issue with computing progress in workers https://github.com/Textualize/textual/pull/2686
- Issues with `switch_screen` not updating the results callback appropriately https://github.com/Textualize/textual/issues/2650
- Fixed incorrect mount order https://github.com/Textualize/textual/pull/2702

### Added

- `work` decorator accepts `description` parameter to add debug string https://github.com/Textualize/textual/issues/2597
- Added `SelectionList` widget https://github.com/Textualize/textual/pull/2652
- `App.AUTO_FOCUS` to set auto focus on all screens https://github.com/Textualize/textual/issues/2594
- Option to `scroll_to_center` to ensure we don't scroll such that the top left corner of the widget is not visible https://github.com/Textualize/textual/pull/2682
- Added `Widget.tooltip` property https://github.com/Textualize/textual/pull/2670
- Added `Region.inflect` https://github.com/Textualize/textual/pull/2670
- `Suggester` API to compose with widgets for automatic suggestions https://github.com/Textualize/textual/issues/2330
- `SuggestFromList` class to let widgets get completions from a fixed set of options https://github.com/Textualize/textual/pull/2604
- `Input` has a new component class `input--suggestion` https://github.com/Textualize/textual/pull/2604
- Added `Widget.remove_children` https://github.com/Textualize/textual/pull/2657
- Added `Validator` framework and validation for `Input` https://github.com/Textualize/textual/pull/2600
- Ability to have private and public validate methods https://github.com/Textualize/textual/pull/2708
- Ability to have private compute methods https://github.com/Textualize/textual/pull/2708
- Added `message_hook` to App.run_test https://github.com/Textualize/textual/pull/2702
- Added `Sparkline` widget https://github.com/Textualize/textual/pull/2631

### Changed

- `Placeholder` now sets its color cycle per app https://github.com/Textualize/textual/issues/2590
- Footer now clears key highlight regardless of whether it's in the active screen or not https://github.com/Textualize/textual/issues/2606
- The default Widget repr no longer displays classes and pseudo-classes (to reduce noise in logs). Add them to your `__rich_repr__` method if needed. https://github.com/Textualize/textual/pull/2623
- Setting `Screen.AUTO_FOCUS` to `None` will inherit `AUTO_FOCUS` from the app instead of disabling it https://github.com/Textualize/textual/issues/2594
- Setting `Screen.AUTO_FOCUS` to `""` will disable it on the screen https://github.com/Textualize/textual/issues/2594
- Messages now have a `handler_name` class var which contains the name of the default handler method.
- `Message.control` is now a property instead of a class variable. https://github.com/Textualize/textual/issues/2528
- `Tree` and `DirectoryTree` Messages no longer accept a `tree` parameter, using `self.node.tree` instead. https://github.com/Textualize/textual/issues/2529
- Keybinding <kbd>right</kbd> in `Input` is also used to accept a suggestion if the cursor is at the end of the input https://github.com/Textualize/textual/pull/2604
- `Input.__init__` now accepts a `suggester` attribute for completion suggestions https://github.com/Textualize/textual/pull/2604
- Using `switch_screen` to switch to the currently active screen is now a no-op https://github.com/Textualize/textual/pull/2692
- Breaking change: removed `reactive.py::Reactive.var` in favor of `reactive.py::var` https://github.com/Textualize/textual/pull/2709/

### Removed

- `Placeholder.reset_color_cycle`
- Removed `Widget.reset_focus` (now called `Widget.blur`) https://github.com/Textualize/textual/issues/2642

## [0.26.0] - 2023-05-20

### Added

- Added `Widget.can_view`

### Changed

- Textual will now scroll focused widgets to center if not in view

## [0.25.0] - 2023-05-17

### Changed

- App `title` and `sub_title` attributes can be set to any type https://github.com/Textualize/textual/issues/2521
- `DirectoryTree` now loads directory contents in a worker https://github.com/Textualize/textual/issues/2456
- Only a single error will be written by default, unless in dev mode ("debug" in App.features) https://github.com/Textualize/textual/issues/2480
- Using `Widget.move_child` where the target and the child being moved are the same is now a no-op https://github.com/Textualize/textual/issues/1743
- Calling `dismiss` on a screen that is not at the top of the stack now raises an exception https://github.com/Textualize/textual/issues/2575
- `MessagePump.call_after_refresh` and `MessagePump.call_later` will now return `False` if the callback could not be scheduled. https://github.com/Textualize/textual/pull/2584

### Fixed

- Fixed `ZeroDivisionError` in `resolve_fraction_unit` https://github.com/Textualize/textual/issues/2502
- Fixed `TreeNode.expand` and `TreeNode.expand_all` not posting a `Tree.NodeExpanded` message https://github.com/Textualize/textual/issues/2535
- Fixed `TreeNode.collapse` and `TreeNode.collapse_all` not posting a `Tree.NodeCollapsed` message https://github.com/Textualize/textual/issues/2535
- Fixed `TreeNode.toggle` and `TreeNode.toggle_all` not posting a `Tree.NodeExpanded` or `Tree.NodeCollapsed` message https://github.com/Textualize/textual/issues/2535
- `footer--description` component class was being ignored https://github.com/Textualize/textual/issues/2544
- Pasting empty selection in `Input` would raise an exception https://github.com/Textualize/textual/issues/2563
- `Screen.AUTO_FOCUS` now focuses the first _focusable_ widget that matches the selector https://github.com/Textualize/textual/issues/2578
- `Screen.AUTO_FOCUS` now works on the default screen on startup https://github.com/Textualize/textual/pull/2581
- Fix for setting dark in App `__init__` https://github.com/Textualize/textual/issues/2583
- Fix issue with scrolling and docks https://github.com/Textualize/textual/issues/2525
- Fix not being able to use CSS classes with `Tab` https://github.com/Textualize/textual/pull/2589

### Added

- Class variable `AUTO_FOCUS` to screens https://github.com/Textualize/textual/issues/2457
- Added `NULL_SPACING` and `NULL_REGION` to geometry.py

## [0.24.1] - 2023-05-08

### Fixed

- Fix TypeError in code browser

## [0.24.0] - 2023-05-08

### Fixed

- Fixed crash when creating a `DirectoryTree` starting anywhere other than `.`
- Fixed line drawing in `Tree` when `Tree.show_root` is `True` https://github.com/Textualize/textual/issues/2397
- Fixed line drawing in `Tree` not marking branches as selected when first getting focus https://github.com/Textualize/textual/issues/2397

### Changed

- The DataTable cursor is now scrolled into view when the cursor coordinate is changed programmatically https://github.com/Textualize/textual/issues/2459
- run_worker exclusive parameter is now `False` by default https://github.com/Textualize/textual/pull/2470
- Added `always_update` as an optional argument for `reactive.var`
- Made Binding description default to empty string, which is equivalent to show=False https://github.com/Textualize/textual/pull/2501
- Modified Message to allow it to be used as a dataclass https://github.com/Textualize/textual/pull/2501
- Decorator `@on` accepts arbitrary `**kwargs` to apply selectors to attributes of the message https://github.com/Textualize/textual/pull/2498

### Added

- Property `control` as alias for attribute `tabs` in `Tabs` messages https://github.com/Textualize/textual/pull/2483
- Experimental: Added "overlay" rule https://github.com/Textualize/textual/pull/2501
- Experimental: Added "constrain" rule https://github.com/Textualize/textual/pull/2501
- Added textual.widgets.Select https://github.com/Textualize/textual/pull/2501
- Added Region.translate_inside https://github.com/Textualize/textual/pull/2501
- `TabbedContent` now takes kwargs `id`, `name`, `classes`, and `disabled`, upon initialization, like other widgets https://github.com/Textualize/textual/pull/2497
- Method `DataTable.move_cursor` https://github.com/Textualize/textual/issues/2472
- Added `OptionList.add_options` https://github.com/Textualize/textual/pull/2508
- Added `TreeNode.is_root` https://github.com/Textualize/textual/pull/2510
- Added `TreeNode.remove_children` https://github.com/Textualize/textual/pull/2510
- Added `TreeNode.remove` https://github.com/Textualize/textual/pull/2510
- Added classvar `Message.ALLOW_SELECTOR_MATCH` https://github.com/Textualize/textual/pull/2498
- Added `ALLOW_SELECTOR_MATCH` to all built-in messages associated with widgets https://github.com/Textualize/textual/pull/2498
- Markdown document sub-widgets now reference the container document
- Table of contents of a markdown document now references the document
- Added the `control` property to messages
  - `DirectoryTree.FileSelected`
  - `ListView`
    - `Highlighted`
    - `Selected`
  - `Markdown`
    - `TableOfContentsUpdated`
    - `TableOfContentsSelected`
    - `LinkClicked`
  - `OptionList`
    - `OptionHighlighted`
    - `OptionSelected`
  - `RadioSet.Changed`
  - `TabContent.TabActivated`
  - `Tree`
    - `NodeSelected`
    - `NodeHighlighted`
    - `NodeExpanded`
    - `NodeCollapsed`

## [0.23.0] - 2023-05-03

### Fixed

- Fixed `outline` top and bottom not handling alpha - https://github.com/Textualize/textual/issues/2371
- Fixed `!important` not applying to `align` https://github.com/Textualize/textual/issues/2420
- Fixed `!important` not applying to `border` https://github.com/Textualize/textual/issues/2420
- Fixed `!important` not applying to `content-align` https://github.com/Textualize/textual/issues/2420
- Fixed `!important` not applying to `outline` https://github.com/Textualize/textual/issues/2420
- Fixed `!important` not applying to `overflow` https://github.com/Textualize/textual/issues/2420
- Fixed `!important` not applying to `scrollbar-size` https://github.com/Textualize/textual/issues/2420
- Fixed `outline-right` not being recognised https://github.com/Textualize/textual/issues/2446
- Fixed OSError when a file system is not available https://github.com/Textualize/textual/issues/2468

### Changed

- Setting attributes with a `compute_` method will now raise an `AttributeError` https://github.com/Textualize/textual/issues/2383
- Unknown psuedo-selectors will now raise a tokenizer error (previously they were silently ignored) https://github.com/Textualize/textual/pull/2445
- Breaking change: `DirectoryTree.FileSelected.path` is now always a `Path` https://github.com/Textualize/textual/issues/2448
- Breaking change: `Directorytree.load_directory` renamed to `Directorytree._load_directory` https://github.com/Textualize/textual/issues/2448
- Unknown pseudo-selectors will now raise a tokenizer error (previously they were silently ignored) https://github.com/Textualize/textual/pull/2445

### Added

- Watch methods can now optionally be private https://github.com/Textualize/textual/issues/2382
- Added `DirectoryTree.path` reactive attribute https://github.com/Textualize/textual/issues/2448
- Added `DirectoryTree.FileSelected.node` https://github.com/Textualize/textual/pull/2463
- Added `DirectoryTree.reload` https://github.com/Textualize/textual/issues/2448
- Added textual.on decorator https://github.com/Textualize/textual/issues/2398

## [0.22.3] - 2023-04-29

### Fixed

- Fixed `textual run` on Windows https://github.com/Textualize/textual/issues/2406
- Fixed top border of button hover state

## [0.22.2] - 2023-04-29

### Added

- Added `TreeNode.tree` as a read-only public attribute https://github.com/Textualize/textual/issues/2413

### Fixed

- Fixed superfluous style updates for focus-within pseudo-selector

## [0.22.1] - 2023-04-28

### Fixed

- Fixed timer issue https://github.com/Textualize/textual/issues/2416
- Fixed `textual run` issue https://github.com/Textualize/textual/issues/2391

## [0.22.0] - 2023-04-27

### Fixed

- Fixed broken fr units when there is a min or max dimension https://github.com/Textualize/textual/issues/2378
- Fixed plain text in Markdown code blocks with no syntax being difficult to read https://github.com/Textualize/textual/issues/2400

### Added

- Added `ProgressBar` widget https://github.com/Textualize/textual/pull/2333

### Changed

- All `textual.containers` are now `1fr` in relevant dimensions by default https://github.com/Textualize/textual/pull/2386


## [0.21.0] - 2023-04-26

### Changed

- `textual run` execs apps in a new context.
- Textual console no longer parses console markup.
- Breaking change: `Container` no longer shows required scrollbars by default https://github.com/Textualize/textual/issues/2361
- Breaking change: `VerticalScroll` no longer shows a required horizontal scrollbar by default
- Breaking change: `HorizontalScroll` no longer shows a required vertical scrollbar by default
- Breaking change: Renamed `App.action_add_class_` to `App.action_add_class`
- Breaking change: Renamed `App.action_remove_class_` to `App.action_remove_class`
- Breaking change: `RadioSet` is now a single focusable widget https://github.com/Textualize/textual/pull/2372
- Breaking change: Removed `containers.Content` (use `containers.VerticalScroll` now)

### Added

- Added `-c` switch to `textual run` which runs commands in a Textual dev environment.
- Breaking change: standard keyboard scrollable navigation bindings have been moved off `Widget` and onto a new base class for scrollable containers (see also below addition) https://github.com/Textualize/textual/issues/2332
- `ScrollView` now inherits from `ScrollableContainer` rather than `Widget` https://github.com/Textualize/textual/issues/2332
- Containers no longer inherit any bindings from `Widget` https://github.com/Textualize/textual/issues/2331
- Added `ScrollableContainer`; a container class that binds the common navigation keys to scroll actions (see also above breaking change) https://github.com/Textualize/textual/issues/2332

### Fixed

- Fixed dark mode toggles in a "child" screen not updating a "parent" screen https://github.com/Textualize/textual/issues/1999
- Fixed "panel" border not exposed via CSS
- Fixed `TabbedContent.active` changes not changing the actual content https://github.com/Textualize/textual/issues/2352
- Fixed broken color on macOS Terminal https://github.com/Textualize/textual/issues/2359

## [0.20.1] - 2023-04-18

### Fix

- New fix for stuck tabs underline https://github.com/Textualize/textual/issues/2229

## [0.20.0] - 2023-04-18

### Changed

- Changed signature of Driver. Technically a breaking change, but unlikely to affect anyone.
- Breaking change: Timer.start is now private, and returns None. There was no reason to call this manually, so unlikely to affect anyone.
- A clicked tab will now be scrolled to the center of its tab container https://github.com/Textualize/textual/pull/2276
- Style updates are now done immediately rather than on_idle https://github.com/Textualize/textual/pull/2304
- `ButtonVariant` is now exported from `textual.widgets.button` https://github.com/Textualize/textual/issues/2264
- `HorizontalScroll` and `VerticalScroll` are now focusable by default https://github.com/Textualize/textual/pull/2317

### Added

- Added `DataTable.remove_row` method https://github.com/Textualize/textual/pull/2253
- option `--port` to the command `textual console` to specify which port the console should connect to https://github.com/Textualize/textual/pull/2258
- `Widget.scroll_to_center` method to scroll children to the center of container widget https://github.com/Textualize/textual/pull/2255 and https://github.com/Textualize/textual/pull/2276
- Added `TabActivated` message to `TabbedContent` https://github.com/Textualize/textual/pull/2260
- Added "panel" border style https://github.com/Textualize/textual/pull/2292
- Added `border-title-color`, `border-title-background`, `border-title-style` rules https://github.com/Textualize/textual/issues/2289
- Added `border-subtitle-color`, `border-subtitle-background`, `border-subtitle-style` rules https://github.com/Textualize/textual/issues/2289

### Fixed

- Fixed order styles are applied in DataTable - allows combining of renderable styles and component classes https://github.com/Textualize/textual/pull/2272
- Fixed key combos with up/down keys in some terminals https://github.com/Textualize/textual/pull/2280
- Fix empty ListView preventing bindings from firing https://github.com/Textualize/textual/pull/2281
- Fix `get_component_styles` returning incorrect values on first call when combined with pseudoclasses https://github.com/Textualize/textual/pull/2304
- Fixed `active_message_pump.get` sometimes resulting in a `LookupError` https://github.com/Textualize/textual/issues/2301

## [0.19.1] - 2023-04-10

### Fixed

- Fix viewport units using wrong viewport size  https://github.com/Textualize/textual/pull/2247
- Fixed layout not clearing arrangement cache https://github.com/Textualize/textual/pull/2249


## [0.19.0] - 2023-04-07

### Added

- Added support for filtering a `DirectoryTree` https://github.com/Textualize/textual/pull/2215

### Changed

- Allowed border_title and border_subtitle to accept Text objects
- Added additional line around titles
- When a container is auto, relative dimensions in children stretch the container. https://github.com/Textualize/textual/pull/2221
- DataTable page up / down now move cursor

### Fixed

- Fixed margin not being respected when width or height is "auto" https://github.com/Textualize/textual/issues/2220
- Fixed issue which prevent scroll_visible from working https://github.com/Textualize/textual/issues/2181
- Fixed missing tracebacks on Windows https://github.com/Textualize/textual/issues/2027

## [0.18.0] - 2023-04-04

### Added

- Added Worker API https://github.com/Textualize/textual/pull/2182

### Changed

- Breaking change: Markdown.update is no longer a coroutine https://github.com/Textualize/textual/pull/2182

### Fixed

- `RadioSet` is now far less likely to report `pressed_button` as `None` https://github.com/Textualize/textual/issues/2203

## [0.17.3] - 2023-04-02

### [Fixed]

- Fixed scrollable area not taking in to account dock https://github.com/Textualize/textual/issues/2188

## [0.17.2] - 2023-04-02

### [Fixed]

- Fixed bindings persistance https://github.com/Textualize/textual/issues/1613
- The `Markdown` widget now auto-increments ordered lists https://github.com/Textualize/textual/issues/2002
- Fixed modal bindings https://github.com/Textualize/textual/issues/2194
- Fix binding enter to active button https://github.com/Textualize/textual/issues/2194

### [Changed]

- tab and shift+tab are now defined on Screen.

## [0.17.1] - 2023-03-30

### Fixed

- Fix cursor not hiding on Windows https://github.com/Textualize/textual/issues/2170
- Fixed freeze when ctrl-clicking links https://github.com/Textualize/textual/issues/2167 https://github.com/Textualize/textual/issues/2073

## [0.17.0] - 2023-03-29

### Fixed

- Issue with parsing action strings whose arguments contained quoted closing parenthesis https://github.com/Textualize/textual/pull/2112
- Issues with parsing action strings with tuple arguments https://github.com/Textualize/textual/pull/2112
- Issue with watching for CSS file changes https://github.com/Textualize/textual/pull/2128
- Fix for tabs not invalidating https://github.com/Textualize/textual/issues/2125
- Fixed scrollbar layers issue https://github.com/Textualize/textual/issues/1358
- Fix for interaction between pseudo-classes and widget-level render caches https://github.com/Textualize/textual/pull/2155

### Changed

- DataTable now has height: auto by default. https://github.com/Textualize/textual/issues/2117
- Textual will now render strings within renderables (such as tables) as Console Markup by default. You can wrap your text with rich.Text() if you want the original behavior. https://github.com/Textualize/textual/issues/2120
- Some widget methods now return `self` instead of `None` https://github.com/Textualize/textual/pull/2102:
  - `Widget`: `refresh`, `focus`, `reset_focus`
  - `Button.press`
  - `DataTable`: `clear`, `refresh_coordinate`, `refresh_row`, `refresh_column`, `sort`
  - `Placehoder.cycle_variant`
  - `Switch.toggle`
  - `Tabs.clear`
  - `TextLog`: `write`, `clear`
  - `TreeNode`: `expand`, `expand_all`, `collapse`, `collapse_all`, `toggle`, `toggle_all`
  - `Tree`: `clear`, `reset`
- Screens with alpha in their background color will now blend with the background. https://github.com/Textualize/textual/pull/2139
- Added "thick" border style. https://github.com/Textualize/textual/pull/2139
- message_pump.app will now set the active app if it is not already set.
- DataTable now has max height set to 100vh

### Added

- Added auto_scroll attribute to TextLog https://github.com/Textualize/textual/pull/2127
- Added scroll_end switch to TextLog.write https://github.com/Textualize/textual/pull/2127
- Added `Widget.get_pseudo_class_state` https://github.com/Textualize/textual/pull/2155
- Added Screen.ModalScreen which prevents App from handling bindings. https://github.com/Textualize/textual/pull/2139
- Added TEXTUAL_LOG env var which should be a path that Textual will write verbose logs to (textual devtools is generally preferred) https://github.com/Textualize/textual/pull/2148
- Added textual.logging.TextualHandler logging handler
- Added Query.set_classes, DOMNode.set_classes, and `classes` setter for Widget https://github.com/Textualize/textual/issues/1081
- Added `OptionList` https://github.com/Textualize/textual/pull/2154

## [0.16.0] - 2023-03-22

### Added
- Added `parser_factory` argument to `Markdown` and `MarkdownViewer` constructors https://github.com/Textualize/textual/pull/2075
- Added `HorizontalScroll` https://github.com/Textualize/textual/issues/1957
- Added `Center` https://github.com/Textualize/textual/issues/1957
- Added `Middle` https://github.com/Textualize/textual/issues/1957
- Added `VerticalScroll` (mimicking the old behaviour of `Vertical`) https://github.com/Textualize/textual/issues/1957
- Added `Widget.border_title` and `Widget.border_subtitle` to set border (sub)title for a widget https://github.com/Textualize/textual/issues/1864
- Added CSS styles `border_title_align` and `border_subtitle_align`.
- Added `TabbedContent` widget https://github.com/Textualize/textual/pull/2059
- Added `get_child_by_type` method to widgets / app https://github.com/Textualize/textual/pull/2059
- Added `Widget.render_str` method https://github.com/Textualize/textual/pull/2059
- Added TEXTUAL_DRIVER environment variable

### Changed

- Dropped "loading-indicator--dot" component style from LoadingIndicator https://github.com/Textualize/textual/pull/2050
- Tabs widget now sends Tabs.Cleared when there is no active tab.
- Breaking change: changed default behaviour of `Vertical` (see `VerticalScroll`) https://github.com/Textualize/textual/issues/1957
- The default `overflow` style for `Horizontal` was changed to `hidden hidden` https://github.com/Textualize/textual/issues/1957
- `DirectoryTree` also accepts `pathlib.Path` objects as the path to list https://github.com/Textualize/textual/issues/1438

### Removed

- Removed `sender` attribute from messages. It's now just private (`_sender`). https://github.com/Textualize/textual/pull/2071

### Fixed

- Fixed borders not rendering correctly. https://github.com/Textualize/textual/pull/2074
- Fix for error when removing nodes. https://github.com/Textualize/textual/issues/2079

## [0.15.1] - 2023-03-14

### Fixed

- Fixed how the namespace for messages is calculated to facilitate inheriting messages https://github.com/Textualize/textual/issues/1814
- `Tab` is now correctly made available from `textual.widgets`. https://github.com/Textualize/textual/issues/2044

## [0.15.0] - 2023-03-13

### Fixed

- Fixed container not resizing when a widget is removed https://github.com/Textualize/textual/issues/2007
- Fixes issue where the horizontal scrollbar would be incorrectly enabled https://github.com/Textualize/textual/pull/2024

## [0.15.0] - 2023-03-13

### Changed

- Fixed container not resizing when a widget is removed https://github.com/Textualize/textual/issues/2007
- Fixed issue where the horizontal scrollbar would be incorrectly enabled https://github.com/Textualize/textual/pull/2024
- Fixed `Pilot.click` not correctly creating the mouse events https://github.com/Textualize/textual/issues/2022
- Fixes issue where the horizontal scrollbar would be incorrectly enabled https://github.com/Textualize/textual/pull/2024
- Fixes for tracebacks not appearing on exit https://github.com/Textualize/textual/issues/2027

### Added

- Added a LoadingIndicator widget https://github.com/Textualize/textual/pull/2018
- Added Tabs Widget https://github.com/Textualize/textual/pull/2020

### Changed

- Breaking change: Renamed Widget.action and App.action to Widget.run_action and App.run_action
- Added `shift`, `meta` and `control` arguments to `Pilot.click`.

## [0.14.0] - 2023-03-09

### Changed

- Breaking change: There is now only `post_message` to post events, which is non-async, `post_message_no_wait` was dropped. https://github.com/Textualize/textual/pull/1940
- Breaking change: The Timer class now has just one method to stop it, `Timer.stop` which is non sync https://github.com/Textualize/textual/pull/1940
- Breaking change: Messages don't require a `sender` in their constructor https://github.com/Textualize/textual/pull/1940
- Many messages have grown a `control` property which returns the control they relate to. https://github.com/Textualize/textual/pull/1940
- Updated styling to make it clear DataTable grows horizontally https://github.com/Textualize/textual/pull/1946
- Changed the `Checkbox` character due to issues with Windows Terminal and Windows 10 https://github.com/Textualize/textual/issues/1934
- Changed the `RadioButton` character due to issues with Windows Terminal and Windows 10 and 11 https://github.com/Textualize/textual/issues/1934
- Changed the `Markdown` initial bullet character due to issues with Windows Terminal and Windows 10 and 11 https://github.com/Textualize/textual/issues/1982
- The underscore `_` is no longer a special alias for the method `pilot.press`

### Added

- Added `data_table` attribute to DataTable events https://github.com/Textualize/textual/pull/1940
- Added `list_view` attribute to `ListView` events https://github.com/Textualize/textual/pull/1940
- Added `radio_set` attribute to `RadioSet` events https://github.com/Textualize/textual/pull/1940
- Added `switch` attribute to `Switch` events https://github.com/Textualize/textual/pull/1940
- Added `hover` and `click` methods to `Pilot` https://github.com/Textualize/textual/pull/1966
- Breaking change: Added `toggle_button` attribute to RadioButton and Checkbox events, replaces `input` https://github.com/Textualize/textual/pull/1940
- A percentage alpha can now be applied to a border https://github.com/Textualize/textual/issues/1863
- Added `Color.multiply_alpha`.
- Added `ContentSwitcher` https://github.com/Textualize/textual/issues/1945

### Fixed

- Fixed bug that prevented pilot from pressing some keys https://github.com/Textualize/textual/issues/1815
- DataTable race condition that caused crash https://github.com/Textualize/textual/pull/1962
- Fixed scrollbar getting "stuck" to cursor when cursor leaves window during drag https://github.com/Textualize/textual/pull/1968 https://github.com/Textualize/textual/pull/2003
- DataTable crash when enter pressed when table is empty https://github.com/Textualize/textual/pull/1973

## [0.13.0] - 2023-03-02

### Added

- Added `Checkbox` https://github.com/Textualize/textual/pull/1872
- Added `RadioButton` https://github.com/Textualize/textual/pull/1872
- Added `RadioSet` https://github.com/Textualize/textual/pull/1872

### Changed

- Widget scrolling methods (such as `Widget.scroll_home` and `Widget.scroll_end`) now perform the scroll after the next refresh https://github.com/Textualize/textual/issues/1774
- Buttons no longer accept arbitrary renderables https://github.com/Textualize/textual/issues/1870

### Fixed

- Scrolling with cursor keys now moves just one cell https://github.com/Textualize/textual/issues/1897
- Fix exceptions in watch methods being hidden on startup https://github.com/Textualize/textual/issues/1886
- Fixed scrollbar size miscalculation https://github.com/Textualize/textual/pull/1910
- Fixed slow exit on some terminals https://github.com/Textualize/textual/issues/1920

## [0.12.1] - 2023-02-25

### Fixed

- Fix for batch update glitch https://github.com/Textualize/textual/pull/1880

## [0.12.0] - 2023-02-24

### Added

- Added `App.batch_update` https://github.com/Textualize/textual/pull/1832
- Added horizontal rule to Markdown https://github.com/Textualize/textual/pull/1832
- Added `Widget.disabled` https://github.com/Textualize/textual/pull/1785
- Added `DOMNode.notify_style_update` to replace `messages.StylesUpdated` message https://github.com/Textualize/textual/pull/1861
- Added `DataTable.show_row_labels` reactive to show and hide row labels https://github.com/Textualize/textual/pull/1868
- Added `DataTable.RowLabelSelected` event, which is emitted when a row label is clicked https://github.com/Textualize/textual/pull/1868
- Added `MessagePump.prevent` context manager to temporarily suppress a given message type https://github.com/Textualize/textual/pull/1866

### Changed

- Scrolling by page now adds to current position.
- Markdown lists have been polished: a selection of bullets, better alignment of numbers, style tweaks https://github.com/Textualize/textual/pull/1832
- Added alternative method of composing Widgets https://github.com/Textualize/textual/pull/1847
- Added `label` parameter to `DataTable.add_row` https://github.com/Textualize/textual/pull/1868
- Breaking change: Some `DataTable` component classes were renamed - see PR for details https://github.com/Textualize/textual/pull/1868

### Removed

- Removed `screen.visible_widgets` and `screen.widgets`
- Removed `StylesUpdate` message. https://github.com/Textualize/textual/pull/1861

### Fixed

- Numbers in a descendant-combined selector no longer cause an error https://github.com/Textualize/textual/issues/1836
- Fixed superfluous scrolling when focusing a docked widget https://github.com/Textualize/textual/issues/1816
- Fixes walk_children which was returning more than one screen https://github.com/Textualize/textual/issues/1846
- Fixed issue with watchers fired for detached nodes https://github.com/Textualize/textual/issues/1846

## [0.11.1] - 2023-02-17

### Fixed

- DataTable fix issue where offset cache was not being used https://github.com/Textualize/textual/pull/1810
- DataTable scrollbars resize correctly when header is toggled https://github.com/Textualize/textual/pull/1803
- DataTable location mapping cleared when clear called https://github.com/Textualize/textual/pull/1809

## [0.11.0] - 2023-02-15

### Added

- Added `TreeNode.expand_all` https://github.com/Textualize/textual/issues/1430
- Added `TreeNode.collapse_all` https://github.com/Textualize/textual/issues/1430
- Added `TreeNode.toggle_all` https://github.com/Textualize/textual/issues/1430
- Added the coroutines `Animator.wait_until_complete` and `pilot.wait_for_scheduled_animations` that allow waiting for all current and scheduled animations https://github.com/Textualize/textual/issues/1658
- Added the method `Animator.is_being_animated` that checks if an attribute of an object is being animated or is scheduled for animation
- Added more keyboard actions and related bindings to `Input` https://github.com/Textualize/textual/pull/1676
- Added App.scroll_sensitivity_x and App.scroll_sensitivity_y to adjust how many lines the scroll wheel moves the scroll position https://github.com/Textualize/textual/issues/928
- Added Shift+scroll wheel and ctrl+scroll wheel to scroll horizontally
- Added `Tree.action_toggle_node` to toggle a node without selecting, and bound it to <kbd>Space</kbd> https://github.com/Textualize/textual/issues/1433
- Added `Tree.reset` to fully reset a `Tree` https://github.com/Textualize/textual/issues/1437
- Added `DataTable.sort` to sort rows https://github.com/Textualize/textual/pull/1638
- Added `DataTable.get_cell` to retrieve a cell by column/row keys https://github.com/Textualize/textual/pull/1638
- Added `DataTable.get_cell_at` to retrieve a cell by coordinate https://github.com/Textualize/textual/pull/1638
- Added `DataTable.update_cell` to update a cell by column/row keys https://github.com/Textualize/textual/pull/1638
- Added `DataTable.update_cell_at` to update a cell at a coordinate  https://github.com/Textualize/textual/pull/1638
- Added `DataTable.ordered_rows` property to retrieve `Row`s as they're currently ordered https://github.com/Textualize/textual/pull/1638
- Added `DataTable.ordered_columns` property to retrieve `Column`s as they're currently ordered https://github.com/Textualize/textual/pull/1638
- Added `DataTable.coordinate_to_cell_key` to find the key for the cell at a coordinate https://github.com/Textualize/textual/pull/1638
- Added `DataTable.is_valid_coordinate` https://github.com/Textualize/textual/pull/1638
- Added `DataTable.is_valid_row_index` https://github.com/Textualize/textual/pull/1638
- Added `DataTable.is_valid_column_index` https://github.com/Textualize/textual/pull/1638
- Added attributes to events emitted from `DataTable` indicating row/column/cell keys https://github.com/Textualize/textual/pull/1638
- Added `DataTable.get_row` to retrieve the values from a row by key https://github.com/Textualize/textual/pull/1786
- Added `DataTable.get_row_at` to retrieve the values from a row by index https://github.com/Textualize/textual/pull/1786
- Added `DataTable.get_column` to retrieve the values from a column by key https://github.com/Textualize/textual/pull/1786
- Added `DataTable.get_column_at` to retrieve the values from a column by index https://github.com/Textualize/textual/pull/1786
- Added `DataTable.HeaderSelected` which is posted when header label clicked https://github.com/Textualize/textual/pull/1788
- Added `DOMNode.watch` and `DOMNode.is_attached` methods  https://github.com/Textualize/textual/pull/1750
- Added `DOMNode.css_tree` which is a renderable that shows the DOM and CSS https://github.com/Textualize/textual/pull/1778
- Added `DOMNode.children_view` which is a view on to a nodes children list, use for querying https://github.com/Textualize/textual/pull/1778
- Added `Markdown` and `MarkdownViewer` widgets.
- Added `--screenshot` option to `textual run`

### Changed

- Breaking change: `TreeNode` can no longer be imported from `textual.widgets`; it is now available via `from textual.widgets.tree import TreeNode`. https://github.com/Textualize/textual/pull/1637
- `Tree` now shows a (subdued) cursor for a highlighted node when focus has moved elsewhere https://github.com/Textualize/textual/issues/1471
- `DataTable.add_row` now accepts `key` argument to uniquely identify the row https://github.com/Textualize/textual/pull/1638
- `DataTable.add_column` now accepts `key` argument to uniquely identify the column https://github.com/Textualize/textual/pull/1638
- `DataTable.add_row` and `DataTable.add_column` now return lists of keys identifying the added rows/columns https://github.com/Textualize/textual/pull/1638
- Breaking change: `DataTable.get_cell_value` renamed to `DataTable.get_value_at` https://github.com/Textualize/textual/pull/1638
- `DataTable.row_count` is now a property https://github.com/Textualize/textual/pull/1638
- Breaking change: `DataTable.cursor_cell` renamed to `DataTable.cursor_coordinate` https://github.com/Textualize/textual/pull/1638
  - The method `validate_cursor_cell` was renamed to `validate_cursor_coordinate`.
  - The method `watch_cursor_cell` was renamed to `watch_cursor_coordinate`.
- Breaking change: `DataTable.hover_cell` renamed to `DataTable.hover_coordinate` https://github.com/Textualize/textual/pull/1638
  - The method `validate_hover_cell` was renamed to `validate_hover_coordinate`.
- Breaking change: `DataTable.data` structure changed, and will be made private in upcoming release https://github.com/Textualize/textual/pull/1638
- Breaking change: `DataTable.refresh_cell` was renamed to `DataTable.refresh_coordinate` https://github.com/Textualize/textual/pull/1638
- Breaking change: `DataTable.get_row_height` now takes a `RowKey` argument instead of a row index https://github.com/Textualize/textual/pull/1638
- Breaking change: `DataTable.data` renamed to `DataTable._data` (it's now private) https://github.com/Textualize/textual/pull/1786
- The `_filter` module was made public (now called `filter`) https://github.com/Textualize/textual/pull/1638
- Breaking change: renamed `Checkbox` to `Switch` https://github.com/Textualize/textual/issues/1746
- `App.install_screen` name is no longer optional https://github.com/Textualize/textual/pull/1778
- `App.query` now only includes the current screen https://github.com/Textualize/textual/pull/1778
- `DOMNode.tree` now displays simple DOM structure only https://github.com/Textualize/textual/pull/1778
- `App.install_screen` now returns None rather than AwaitMount https://github.com/Textualize/textual/pull/1778
- `DOMNode.children` is now a simple sequence, the NodesList is exposed as `DOMNode._nodes` https://github.com/Textualize/textual/pull/1778
- `DataTable` cursor can now enter fixed columns https://github.com/Textualize/textual/pull/1799

### Fixed

- Fixed stuck screen  https://github.com/Textualize/textual/issues/1632
- Fixed programmatic style changes not refreshing children layouts when parent widget did not change size https://github.com/Textualize/textual/issues/1607
- Fixed relative units in `grid-rows` and `grid-columns` being computed with respect to the wrong dimension https://github.com/Textualize/textual/issues/1406
- Fixed bug with animations that were triggered back to back, where the second one wouldn't start https://github.com/Textualize/textual/issues/1372
- Fixed bug with animations that were scheduled where all but the first would be skipped https://github.com/Textualize/textual/issues/1372
- Programmatically setting `overflow_x`/`overflow_y` refreshes the layout correctly https://github.com/Textualize/textual/issues/1616
- Fixed double-paste into `Input` https://github.com/Textualize/textual/issues/1657
- Added a workaround for an apparent Windows Terminal paste issue https://github.com/Textualize/textual/issues/1661
- Fixed issue with renderable width calculation https://github.com/Textualize/textual/issues/1685
- Fixed issue with app not processing Paste event https://github.com/Textualize/textual/issues/1666
- Fixed glitch with view position with auto width inputs https://github.com/Textualize/textual/issues/1693
- Fixed `DataTable` "selected" events containing wrong coordinates when mouse was used https://github.com/Textualize/textual/issues/1723

### Removed

- Methods `MessagePump.emit` and `MessagePump.emit_no_wait` https://github.com/Textualize/textual/pull/1738
- Removed `reactive.watch` in favor of DOMNode.watch.

## [0.10.1] - 2023-01-20

### Added

- Added Strip.text property https://github.com/Textualize/textual/issues/1620

### Fixed

- Fixed `textual diagnose` crash on older supported Python versions. https://github.com/Textualize/textual/issues/1622

### Changed

- The default filename for screenshots uses a datetime format similar to ISO8601, but with reserved characters replaced by underscores https://github.com/Textualize/textual/pull/1518


## [0.10.0] - 2023-01-19

### Added

- Added `TreeNode.parent` -- a read-only property for accessing a node's parent https://github.com/Textualize/textual/issues/1397
- Added public `TreeNode` label access via `TreeNode.label` https://github.com/Textualize/textual/issues/1396
- Added read-only public access to the children of a `TreeNode` via `TreeNode.children` https://github.com/Textualize/textual/issues/1398
- Added `Tree.get_node_by_id` to allow getting a node by its ID https://github.com/Textualize/textual/pull/1535
- Added a `Tree.NodeHighlighted` message, giving a `on_tree_node_highlighted` event handler https://github.com/Textualize/textual/issues/1400
- Added a `inherit_component_classes` subclassing parameter to control whether component classes are inherited from base classes https://github.com/Textualize/textual/issues/1399
- Added `diagnose` as a `textual` command https://github.com/Textualize/textual/issues/1542
- Added `row` and `column` cursors to `DataTable` https://github.com/Textualize/textual/pull/1547
- Added an optional parameter `selector` to the methods `Screen.focus_next` and `Screen.focus_previous` that enable using a CSS selector to narrow down which widgets can get focus https://github.com/Textualize/textual/issues/1196

### Changed

- `MouseScrollUp` and `MouseScrollDown` now inherit from `MouseEvent` and have attached modifier keys. https://github.com/Textualize/textual/pull/1458
- Fail-fast and print pretty tracebacks for Widget compose errors https://github.com/Textualize/textual/pull/1505
- Added Widget._refresh_scroll to avoid expensive layout when scrolling https://github.com/Textualize/textual/pull/1524
- `events.Paste` now bubbles https://github.com/Textualize/textual/issues/1434
- Improved error message when style flag `none` is mixed with other flags (e.g., when setting `text-style`) https://github.com/Textualize/textual/issues/1420
- Clock color in the `Header` widget now matches the header color https://github.com/Textualize/textual/issues/1459
- Programmatic calls to scroll now optionally scroll even if overflow styling says otherwise (introduces a new `force` parameter to all the `scroll_*` methods) https://github.com/Textualize/textual/issues/1201
- `COMPONENT_CLASSES` are now inherited from base classes https://github.com/Textualize/textual/issues/1399
- Watch methods may now take no parameters
- Added `compute` parameter to reactive
- A `TypeError` raised during `compose` now carries the full traceback
- Removed base class `NodeMessage` from which all node-related `Tree` events inherited

### Fixed

- The styles `scrollbar-background-active` and `scrollbar-color-hover` are no longer ignored https://github.com/Textualize/textual/pull/1480
- The widget `Placeholder` can now have its width set to `auto` https://github.com/Textualize/textual/pull/1508
- Behavior of widget `Input` when rendering after programmatic value change and related scenarios https://github.com/Textualize/textual/issues/1477 https://github.com/Textualize/textual/issues/1443
- `DataTable.show_cursor` now correctly allows cursor toggling https://github.com/Textualize/textual/pull/1547
- Fixed cursor not being visible on `DataTable` mount when `fixed_columns` were used https://github.com/Textualize/textual/pull/1547
- Fixed `DataTable` cursors not resetting to origin on `clear()` https://github.com/Textualize/textual/pull/1601
- Fixed TextLog wrapping issue https://github.com/Textualize/textual/issues/1554
- Fixed issue with TextLog not writing anything before layout https://github.com/Textualize/textual/issues/1498
- Fixed an exception when populating a child class of `ListView` purely from `compose` https://github.com/Textualize/textual/issues/1588
- Fixed freeze in tests https://github.com/Textualize/textual/issues/1608
- Fixed minus not displaying as symbol https://github.com/Textualize/textual/issues/1482

## [0.9.1] - 2022-12-30

### Added

- Added textual._win_sleep for Python on Windows < 3.11 https://github.com/Textualize/textual/pull/1457

## [0.9.0] - 2022-12-30

### Added

- Added textual.strip.Strip primitive
- Added textual._cache.FIFOCache
- Added an option to clear columns in DataTable.clear() https://github.com/Textualize/textual/pull/1427

### Changed

- Widget.render_line now returns a Strip
- Fix for slow updates on Windows
- Bumped Rich dependency

## [0.8.2] - 2022-12-28

### Fixed

- Fixed issue with TextLog.clear() https://github.com/Textualize/textual/issues/1447

## [0.8.1] - 2022-12-25

### Fixed

- Fix for overflowing tree issue https://github.com/Textualize/textual/issues/1425

## [0.8.0] - 2022-12-22

### Fixed

- Fixed issues with nested auto dimensions https://github.com/Textualize/textual/issues/1402
- Fixed watch method incorrectly running on first set when value hasn't changed and init=False https://github.com/Textualize/textual/pull/1367
- `App.dark` can now be set from `App.on_load` without an error being raised  https://github.com/Textualize/textual/issues/1369
- Fixed setting `visibility` changes needing a `refresh` https://github.com/Textualize/textual/issues/1355

### Added

- Added `textual.actions.SkipAction` exception which can be raised from an action to allow parents to process bindings.
- Added `textual keys` preview.
- Added ability to bind to a character in addition to key name. i.e. you can bind to "." or "full_stop".
- Added TextLog.shrink attribute to allow renderable to reduce in size to fit width.

### Changed

- Deprecated `PRIORITY_BINDINGS` class variable.
- Renamed `char` to `character` on Key event.
- Renamed `key_name` to `name` on Key event.
- Queries/`walk_children` no longer includes self in results by default https://github.com/Textualize/textual/pull/1416

## [0.7.0] - 2022-12-17

### Added

- Added `PRIORITY_BINDINGS` class variable, which can be used to control if a widget's bindings have priority by default. https://github.com/Textualize/textual/issues/1343

### Changed

- Renamed the `Binding` argument `universal` to `priority`. https://github.com/Textualize/textual/issues/1343
- When looking for bindings that have priority, they are now looked from `App` downwards. https://github.com/Textualize/textual/issues/1343
- `BINDINGS` on an `App`-derived class have priority by default. https://github.com/Textualize/textual/issues/1343
- `BINDINGS` on a `Screen`-derived class have priority by default. https://github.com/Textualize/textual/issues/1343
- Added a message parameter to Widget.exit

### Fixed

- Fixed validator not running on first reactive set https://github.com/Textualize/textual/pull/1359
- Ensure only printable characters are used as key_display https://github.com/Textualize/textual/pull/1361


## [0.6.0] - 2022-12-11

https://textual.textualize.io/blog/2022/12/11/version-060

### Added

- Added "inherited bindings" -- BINDINGS classvar will be merged with base classes, unless inherit_bindings is set to False
- Added `Tree` widget which replaces `TreeControl`.
- Added widget `Placeholder` https://github.com/Textualize/textual/issues/1200.
- Added `ListView` and `ListItem` widgets https://github.com/Textualize/textual/pull/1143

### Changed

- Rebuilt `DirectoryTree` with new `Tree` control.
- Empty containers with a dimension set to `"auto"` will now collapse instead of filling up the available space.
- Container widgets now have default height of `1fr`.
- The default `width` of a `Label` is now `auto`.

### Fixed

- Type selectors can now contain numbers https://github.com/Textualize/textual/issues/1253
- Fixed visibility not affecting children https://github.com/Textualize/textual/issues/1313
- Fixed issue with auto width/height and relative children https://github.com/Textualize/textual/issues/1319
- Fixed issue with offset applied to containers https://github.com/Textualize/textual/issues/1256
- Fixed default CSS retrieval for widgets with no `DEFAULT_CSS` that inherited from widgets with `DEFAULT_CSS` https://github.com/Textualize/textual/issues/1335
- Fixed merging of `BINDINGS` when binding inheritance is set to `None` https://github.com/Textualize/textual/issues/1351

## [0.5.0] - 2022-11-20

### Added

- Add get_child_by_id and get_widget_by_id, remove get_child https://github.com/Textualize/textual/pull/1146
- Add easing parameter to Widget.scroll_* methods https://github.com/Textualize/textual/pull/1144
- Added Widget.call_later which invokes a callback on idle.
- `DOMNode.ancestors` no longer includes `self`.
- Added `DOMNode.ancestors_with_self`, which retains the old behaviour of
  `DOMNode.ancestors`.
- Improved the speed of `DOMQuery.remove`.
- Added DataTable.clear
- Added low-level `textual.walk` methods.
- It is now possible to `await` a `Widget.remove`.
  https://github.com/Textualize/textual/issues/1094
- It is now possible to `await` a `DOMQuery.remove`. Note that this changes
  the return value of `DOMQuery.remove`, which used to return `self`.
  https://github.com/Textualize/textual/issues/1094
- Added Pilot.wait_for_animation
- Added `Widget.move_child` https://github.com/Textualize/textual/issues/1121
- Added a `Label` widget https://github.com/Textualize/textual/issues/1190
- Support lazy-instantiated Screens (callables in App.SCREENS) https://github.com/Textualize/textual/pull/1185
- Display of keys in footer has more sensible defaults https://github.com/Textualize/textual/pull/1213
- Add App.get_key_display, allowing custom key_display App-wide https://github.com/Textualize/textual/pull/1213

### Changed

- Watchers are now called immediately when setting the attribute if they are synchronous. https://github.com/Textualize/textual/pull/1145
- Widget.call_later has been renamed to Widget.call_after_refresh.
- Button variant values are now checked at runtime. https://github.com/Textualize/textual/issues/1189
- Added caching of some properties in Styles object

### Fixed

- Fixed DataTable row not updating after add https://github.com/Textualize/textual/issues/1026
- Fixed issues with animation. Now objects of different types may be animated.
- Fixed containers with transparent background not showing borders https://github.com/Textualize/textual/issues/1175
- Fixed auto-width in horizontal containers https://github.com/Textualize/textual/pull/1155
- Fixed Input cursor invisible when placeholder empty https://github.com/Textualize/textual/pull/1202
- Fixed deadlock when removing widgets from the App https://github.com/Textualize/textual/pull/1219

## [0.4.0] - 2022-11-08

https://textual.textualize.io/blog/2022/11/08/version-040/#version-040

### Changed

- Dropped support for mounting "named" and "anonymous" widgets via
  `App.mount` and `Widget.mount`. Both methods now simply take one or more
  widgets as positional arguments.
- `DOMNode.query_one` now raises a `TooManyMatches` exception if there is
  more than one matching node.
  https://github.com/Textualize/textual/issues/1096
- `App.mount` and `Widget.mount` have new `before` and `after` parameters https://github.com/Textualize/textual/issues/778

### Added

- Added `init` param to reactive.watch
- `CSS_PATH` can now be a list of CSS files https://github.com/Textualize/textual/pull/1079
- Added `DOMQuery.only_one` https://github.com/Textualize/textual/issues/1096
- Writes to stdout are now done in a thread, for smoother animation. https://github.com/Textualize/textual/pull/1104

## [0.3.0] - 2022-10-31

### Fixed

- Fixed issue where scrollbars weren't being unmounted
- Fixed fr units for horizontal and vertical layouts https://github.com/Textualize/textual/pull/1067
- Fixed `textual run` breaking sys.argv https://github.com/Textualize/textual/issues/1064
- Fixed footer not updating styles when toggling dark mode
- Fixed how the app title in a `Header` is centred https://github.com/Textualize/textual/issues/1060
- Fixed the swapping of button variants https://github.com/Textualize/textual/issues/1048
- Fixed reserved characters in screenshots https://github.com/Textualize/textual/issues/993
- Fixed issue with TextLog max_lines https://github.com/Textualize/textual/issues/1058

### Changed

- DOMQuery now raises InvalidQueryFormat in response to invalid query strings, rather than cryptic CSS error
- Dropped quit_after, screenshot, and screenshot_title from App.run, which can all be done via auto_pilot
- Widgets are now closed in reversed DOM order
- Input widget justify hardcoded to left to prevent text-align interference
- Changed `textual run` so that it patches `argv` in more situations
- DOM classes and IDs are now always treated fully case-sensitive https://github.com/Textualize/textual/issues/1047

### Added

- Added Unmount event
- Added App.run_async method
- Added App.run_test context manager
- Added auto_pilot to App.run and App.run_async
- Added Widget._get_virtual_dom to get scrollbars
- Added size parameter to run and run_async
- Added always_update to reactive
- Returned an awaitable from push_screen, switch_screen, and install_screen https://github.com/Textualize/textual/pull/1061

## [0.2.1] - 2022-10-23

### Changed

- Updated meta data for PyPI

## [0.2.0] - 2022-10-23

### Added

- CSS support
- Too numerous to mention
## [0.1.18] - 2022-04-30

### Changed

- Bump typing extensions

## [0.1.17] - 2022-03-10

### Changed

- Bumped Rich dependency

## [0.1.16] - 2022-03-10

### Fixed

- Fixed escape key hanging on Windows

## [0.1.15] - 2022-01-31

### Added

- Added Windows Driver

## [0.1.14] - 2022-01-09

### Changed

- Updated Rich dependency to 11.X

## [0.1.13] - 2022-01-01

### Fixed

- Fixed spurious characters when exiting app
- Fixed increasing delay when exiting

## [0.1.12] - 2021-09-20

### Added

- Added geometry.Spacing

### Fixed

- Fixed calculation of virtual size in scroll views

## [0.1.11] - 2021-09-12

### Changed

- Changed message handlers to use prefix handle\_
- Renamed messages to drop the Message suffix
- Events now bubble by default
- Refactor of layout

### Added

- Added App.measure
- Added auto_width to Vertical Layout, WindowView, an ScrollView
- Added big_table.py example
- Added easing.py example

## [0.1.10] - 2021-08-25

### Added

- Added keyboard control of tree control
- Added Widget.gutter to calculate space between renderable and outside edge
- Added margin, padding, and border attributes to Widget

### Changed

- Callbacks may be async or non-async.
- Event handler event argument is optional.
- Fixed exception in clock example https://github.com/willmcgugan/textual/issues/52
- Added Message.wait() which waits for a message to be processed
- Key events are now sent to widgets first, before processing bindings

## [0.1.9] - 2021-08-06

### Added

- Added hover over and mouse click to activate keys in footer
- Added verbosity argument to Widget.log

### Changed

- Simplified events. Remove Startup event (use Mount)
- Changed geometry.Point to geometry.Offset and geometry.Dimensions to geometry.Size

## [0.1.8] - 2021-07-17

### Fixed

- Fixed exiting mouse mode
- Fixed slow animation

### Added

- New log system

## [0.1.7] - 2021-07-14

### Changed

- Added functionality to calculator example.
- Scrollview now shows scrollbars automatically
- New handler system for messages that doesn't require inheritance
- Improved traceback handling

[0.83.0]: https://github.com/Textualize/textual/compare/v0.82.0...v0.83.0
[0.82.0]: https://github.com/Textualize/textual/compare/v0.81.0...v0.82.0
[0.81.0]: https://github.com/Textualize/textual/compare/v0.80.1...v0.81.0
[0.80.1]: https://github.com/Textualize/textual/compare/v0.80.0...v0.80.1
[0.80.0]: https://github.com/Textualize/textual/compare/v0.79.0...v0.80.0
[0.79.0]: https://github.com/Textualize/textual/compare/v0.78.0...v0.79.0
[0.78.0]: https://github.com/Textualize/textual/compare/v0.77.0...v0.78.0
[0.77.0]: https://github.com/Textualize/textual/compare/v0.76.0...v0.77.0
[0.76.0]: https://github.com/Textualize/textual/compare/v0.75.1...v0.76.0
[0.75.1]: https://github.com/Textualize/textual/compare/v0.75.0...v0.75.1
[0.75.0]: https://github.com/Textualize/textual/compare/v0.74.0...v0.75.0
[0.74.0]: https://github.com/Textualize/textual/compare/v0.73.0...v0.74.0
[0.73.0]: https://github.com/Textualize/textual/compare/v0.72.0...v0.73.0
[0.72.0]: https://github.com/Textualize/textual/compare/v0.71.0...v0.72.0
[0.71.0]: https://github.com/Textualize/textual/compare/v0.70.0...v0.71.0
[0.70.0]: https://github.com/Textualize/textual/compare/v0.69.0...v0.70.0
[0.69.0]: https://github.com/Textualize/textual/compare/v0.68.0...v0.69.0
[0.68.0]: https://github.com/Textualize/textual/compare/v0.67.1...v0.68.0
[0.67.1]: https://github.com/Textualize/textual/compare/v0.67.0...v0.67.1
[0.67.0]: https://github.com/Textualize/textual/compare/v0.66.0...v0.67.0
[0.66.0]: https://github.com/Textualize/textual/compare/v0.65.2...v0.66.0
[0.65.2]: https://github.com/Textualize/textual/compare/v0.65.1...v0.65.2
[0.65.1]: https://github.com/Textualize/textual/compare/v0.65.0...v0.65.1
[0.65.0]: https://github.com/Textualize/textual/compare/v0.64.0...v0.65.0
[0.64.0]: https://github.com/Textualize/textual/compare/v0.63.6...v0.64.0
[0.63.6]: https://github.com/Textualize/textual/compare/v0.63.5...v0.63.6
[0.63.5]: https://github.com/Textualize/textual/compare/v0.63.4...v0.63.5
[0.63.4]: https://github.com/Textualize/textual/compare/v0.63.3...v0.63.4
[0.63.3]: https://github.com/Textualize/textual/compare/v0.63.2...v0.63.3
[0.63.2]: https://github.com/Textualize/textual/compare/v0.63.1...v0.63.2
[0.63.1]: https://github.com/Textualize/textual/compare/v0.63.0...v0.63.1
[0.63.0]: https://github.com/Textualize/textual/compare/v0.62.0...v0.63.0
[0.62.0]: https://github.com/Textualize/textual/compare/v0.61.1...v0.62.0
[0.61.1]: https://github.com/Textualize/textual/compare/v0.61.0...v0.61.1
[0.61.0]: https://github.com/Textualize/textual/compare/v0.60.1...v0.61.0
[0.60.1]: https://github.com/Textualize/textual/compare/v0.60.0...v0.60.1
[0.60.0]: https://github.com/Textualize/textual/compare/v0.59.0...v0.60.0
[0.59.0]: https://github.com/Textualize/textual/compare/v0.58.1...v0.59.0
[0.58.1]: https://github.com/Textualize/textual/compare/v0.58.0...v0.58.1
[0.58.0]: https://github.com/Textualize/textual/compare/v0.57.1...v0.58.0
[0.57.1]: https://github.com/Textualize/textual/compare/v0.57.0...v0.57.1
[0.57.0]: https://github.com/Textualize/textual/compare/v0.56.3...v0.57.0
[0.56.3]: https://github.com/Textualize/textual/compare/v0.56.2...v0.56.3
[0.56.2]: https://github.com/Textualize/textual/compare/v0.56.1...v0.56.2
[0.56.1]: https://github.com/Textualize/textual/compare/v0.56.0...v0.56.1
[0.56.0]: https://github.com/Textualize/textual/compare/v0.55.1...v0.56.0
[0.55.1]: https://github.com/Textualize/textual/compare/v0.55.0...v0.55.1
[0.55.0]: https://github.com/Textualize/textual/compare/v0.54.0...v0.55.0
[0.54.0]: https://github.com/Textualize/textual/compare/v0.53.1...v0.54.0
[0.53.1]: https://github.com/Textualize/textual/compare/v0.53.0...v0.53.1
[0.53.0]: https://github.com/Textualize/textual/compare/v0.52.1...v0.53.0
[0.52.1]: https://github.com/Textualize/textual/compare/v0.52.0...v0.52.1
[0.52.0]: https://github.com/Textualize/textual/compare/v0.51.0...v0.52.0
[0.51.0]: https://github.com/Textualize/textual/compare/v0.50.1...v0.51.0
[0.50.1]: https://github.com/Textualize/textual/compare/v0.50.0...v0.50.1
[0.50.0]: https://github.com/Textualize/textual/compare/v0.49.0...v0.50.0
[0.49.1]: https://github.com/Textualize/textual/compare/v0.49.0...v0.49.1
[0.49.0]: https://github.com/Textualize/textual/compare/v0.48.2...v0.49.0
[0.48.2]: https://github.com/Textualize/textual/compare/v0.48.1...v0.48.2
[0.48.1]: https://github.com/Textualize/textual/compare/v0.48.0...v0.48.1
[0.48.0]: https://github.com/Textualize/textual/compare/v0.47.1...v0.48.0
[0.47.1]: https://github.com/Textualize/textual/compare/v0.47.0...v0.47.1
[0.47.0]: https://github.com/Textualize/textual/compare/v0.46.0...v0.47.0
[0.46.0]: https://github.com/Textualize/textual/compare/v0.45.1...v0.46.0
[0.45.1]: https://github.com/Textualize/textual/compare/v0.45.0...v0.45.1
[0.45.0]: https://github.com/Textualize/textual/compare/v0.44.1...v0.45.0
[0.44.1]: https://github.com/Textualize/textual/compare/v0.44.0...v0.44.1
[0.44.0]: https://github.com/Textualize/textual/compare/v0.43.2...v0.44.0
[0.43.2]: https://github.com/Textualize/textual/compare/v0.43.1...v0.43.2
[0.43.1]: https://github.com/Textualize/textual/compare/v0.43.0...v0.43.1
[0.43.0]: https://github.com/Textualize/textual/compare/v0.42.0...v0.43.0
[0.42.0]: https://github.com/Textualize/textual/compare/v0.41.0...v0.42.0
[0.41.0]: https://github.com/Textualize/textual/compare/v0.40.0...v0.41.0
[0.40.0]: https://github.com/Textualize/textual/compare/v0.39.0...v0.40.0
[0.39.0]: https://github.com/Textualize/textual/compare/v0.38.1...v0.39.0
[0.38.1]: https://github.com/Textualize/textual/compare/v0.38.0...v0.38.1
[0.38.0]: https://github.com/Textualize/textual/compare/v0.37.1...v0.38.0
[0.37.1]: https://github.com/Textualize/textual/compare/v0.37.0...v0.37.1
[0.37.0]: https://github.com/Textualize/textual/compare/v0.36.0...v0.37.0
[0.36.0]: https://github.com/Textualize/textual/compare/v0.35.1...v0.36.0
[0.35.1]: https://github.com/Textualize/textual/compare/v0.35.0...v0.35.1
[0.35.0]: https://github.com/Textualize/textual/compare/v0.34.0...v0.35.0
[0.34.0]: https://github.com/Textualize/textual/compare/v0.33.0...v0.34.0
[0.33.0]: https://github.com/Textualize/textual/compare/v0.32.0...v0.33.0
[0.32.0]: https://github.com/Textualize/textual/compare/v0.31.0...v0.32.0
[0.31.0]: https://github.com/Textualize/textual/compare/v0.30.0...v0.31.0
[0.30.0]: https://github.com/Textualize/textual/compare/v0.29.0...v0.30.0
[0.29.0]: https://github.com/Textualize/textual/compare/v0.28.1...v0.29.0
[0.28.1]: https://github.com/Textualize/textual/compare/v0.28.0...v0.28.1
[0.28.0]: https://github.com/Textualize/textual/compare/v0.27.0...v0.28.0
[0.27.0]: https://github.com/Textualize/textual/compare/v0.26.0...v0.27.0
[0.26.0]: https://github.com/Textualize/textual/compare/v0.25.0...v0.26.0
[0.25.0]: https://github.com/Textualize/textual/compare/v0.24.1...v0.25.0
[0.24.1]: https://github.com/Textualize/textual/compare/v0.24.0...v0.24.1
[0.24.0]: https://github.com/Textualize/textual/compare/v0.23.0...v0.24.0
[0.23.0]: https://github.com/Textualize/textual/compare/v0.22.3...v0.23.0
[0.22.3]: https://github.com/Textualize/textual/compare/v0.22.2...v0.22.3
[0.22.2]: https://github.com/Textualize/textual/compare/v0.22.1...v0.22.2
[0.22.1]: https://github.com/Textualize/textual/compare/v0.22.0...v0.22.1
[0.22.0]: https://github.com/Textualize/textual/compare/v0.21.0...v0.22.0
[0.21.0]: https://github.com/Textualize/textual/compare/v0.20.1...v0.21.0
[0.20.1]: https://github.com/Textualize/textual/compare/v0.20.0...v0.20.1
[0.20.0]: https://github.com/Textualize/textual/compare/v0.19.1...v0.20.0
[0.19.1]: https://github.com/Textualize/textual/compare/v0.19.0...v0.19.1
[0.19.0]: https://github.com/Textualize/textual/compare/v0.18.0...v0.19.0
[0.18.0]: https://github.com/Textualize/textual/compare/v0.17.4...v0.18.0
[0.17.3]: https://github.com/Textualize/textual/compare/v0.17.2...v0.17.3
[0.17.2]: https://github.com/Textualize/textual/compare/v0.17.1...v0.17.2
[0.17.1]: https://github.com/Textualize/textual/compare/v0.17.0...v0.17.1
[0.17.0]: https://github.com/Textualize/textual/compare/v0.16.0...v0.17.0
[0.16.0]: https://github.com/Textualize/textual/compare/v0.15.1...v0.16.0
[0.15.1]: https://github.com/Textualize/textual/compare/v0.15.0...v0.15.1
[0.15.0]: https://github.com/Textualize/textual/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/Textualize/textual/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/Textualize/textual/compare/v0.12.1...v0.13.0
[0.12.1]: https://github.com/Textualize/textual/compare/v0.12.0...v0.12.1
[0.12.0]: https://github.com/Textualize/textual/compare/v0.11.1...v0.12.0
[0.11.1]: https://github.com/Textualize/textual/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/Textualize/textual/compare/v0.10.1...v0.11.0
[0.10.1]: https://github.com/Textualize/textual/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/Textualize/textual/compare/v0.9.1...v0.10.0
[0.9.1]: https://github.com/Textualize/textual/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/Textualize/textual/compare/v0.8.2...v0.9.0
[0.8.2]: https://github.com/Textualize/textual/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/Textualize/textual/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/Textualize/textual/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/Textualize/textual/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/Textualize/textual/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/Textualize/textual/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Textualize/textual/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Textualize/textual/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/Textualize/textual/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/Textualize/textual/compare/v0.1.18...v0.2.0
[0.1.18]: https://github.com/Textualize/textual/compare/v0.1.17...v0.1.18
[0.1.17]: https://github.com/Textualize/textual/compare/v0.1.16...v0.1.17
[0.1.16]: https://github.com/Textualize/textual/compare/v0.1.15...v0.1.16
[0.1.15]: https://github.com/Textualize/textual/compare/v0.1.14...v0.1.15
[0.1.14]: https://github.com/Textualize/textual/compare/v0.1.13...v0.1.14
[0.1.13]: https://github.com/Textualize/textual/compare/v0.1.12...v0.1.13
[0.1.12]: https://github.com/Textualize/textual/compare/v0.1.11...v0.1.12
[0.1.11]: https://github.com/Textualize/textual/compare/v0.1.10...v0.1.11
[0.1.10]: https://github.com/Textualize/textual/compare/v0.1.9...v0.1.10
[0.1.9]: https://github.com/Textualize/textual/compare/v0.1.8...v0.1.9
[0.1.8]: https://github.com/Textualize/textual/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/Textualize/textual/releases/tag/v0.1.7
