The NetKAN consists of CKAN fragments which are used by our indexing bots to generate metadata for use by the CKAN client and other tools.

Contributing to the NetKAN is the preferred way to add CKAN support for a mod, as it needs only be done once, and our bots will automatically pick up new releaes.  This is the preferred way to index CKAN mods. The files themselves live inside the `NetKAN` folder.

The format of NetKAN files is that described in the [CKAN Spec](https://github.com/KSP-CKAN/CKAN/blob/master/Spec.md), *including* the special use fields at the end.

To inflate a NetKAN file into a CKAN file, simply give it as an argument to the [`netkan.exe`](https://github.com/KSP-CKAN/CKAN/releases) executable. The same executable works on all systems (Mac/Linux/Windows), and requires mono 4.0 to run.

All contributions to this repository *must* me made under a CC-0 license. Pull requests are very welcome.
