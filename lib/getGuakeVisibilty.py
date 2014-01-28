from gi.repository import Gtk, Wnck

Gtk.init([])  # necessary only if not using a Gtk.main() loop
screen = Wnck.Screen.get_default()
screen.force_update()  # recommended per Wnck documentation

visibility = False

# loop all windows
for window in screen.get_windows():
    if window.get_name() == 'Guake!':
        visibility = True

# clean up Wnck (saves resources, check documentation)
window = None
screen = None
Wnck.shutdown()

print visibility
