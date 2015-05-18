package Test::NetKAN;

use strict;
use warnings;
use parent 'Exporter';

use FindBin qw($Bin);
use JSON::Any;
use Test::More;

our @EXPORT_OK = qw(netkan_files read_netkan licenses);

=head2 netkan_files

Returns a hash mapping `shortname => filename` for the NetKAN
directory.

=cut

sub netkan_files {

    my %files;

    foreach my $filename (glob(qq{"$Bin/../NetKAN/*.netkan"})) {
        my ($shortname) = ($filename =~ m{([^/]+)\.netkan$});

        if (!$shortname) {
            diag "Skipping oddly named file - $filename\n";
            next;
        }

        $files{$shortname} = $filename;
    }

    return %files;
}

=head2 read_netkan

Given a filename, returns the decoded data-structure inside it.

=cut

sub read_netkan {
    my ($filename) = @_;
    local $/;

    open(my $fh, '<', $filename);

    return JSON::Any->new->decode(<$fh>);
}

=head licenses

Returns a hash containing a list of valid licenses as keys. Values
are all merely '1' (true).

=cut

sub licenses {
    my %licenses;
    
    # Populate our hash with the fields shamelessly torn from
    # CKAN.schema
    @licenses{
        "public-domain",
        "Apache", "Apache-1.0", "Apache-2.0",
        "Artistic", "Artistic-1.0", "Artistic-2.0",
        "BSD-2-clause", "BSD-3-clause", "BSD-4-clause",
        "ISC",
        "CC-BY", "CC-BY-1.0", "CC-BY-2.0", "CC-BY-2.5", "CC-BY-3.0", "CC-BY-4.0",
        "CC-BY-SA", "CC-BY-SA-1.0", "CC-BY-SA-2.0", "CC-BY-SA-2.5", "CC-BY-SA-3.0", "CC-BY-SA-4.0",
        "CC-BY-NC", "CC-BY-NC-1.0", "CC-BY-NC-2.0", "CC-BY-NC-2.5", "CC-BY-NC-3.0", "CC-BY-NC-4.0",
        "CC-BY-NC-SA", "CC-BY-NC-SA-1.0", "CC-BY-NC-SA-2.0", "CC-BY-NC-SA-2.5", "CC-BY-NC-SA-3.0", "CC-BY-NC-SA-4.0",
        "CC-BY-NC-ND", "CC-BY-NC-ND-1.0", "CC-BY-NC-ND-2.0", "CC-BY-NC-ND-2.5", "CC-BY-NC-ND-3.0", "CC-BY-NC-ND-4.0",
        "CC0",
        "CDDL", "CPL",
        "EFL-1.0", "EFL-2.0",
        "Expat", "MIT",
        "GPL-1.0", "GPL-2.0", "GPL-3.0",
        "LGPL-2.0", "LGPL-2.1", "LGPL-3.0",
        "GFDL-1.0", "GFDL-1.1", "GFDL-1.2", "GFDL-1.3",
        "GFDL-NIV-1.0", "GFDL-NIV-1.1", "GFDL-NIV-1.2", "GFDL-NIV-1.3",
        "LPPL-1.0", "LPPL-1.1", "LPPL-1.2", "LPPL-1.3c",
        "MPL-1.1",
        "Perl",
        "Python-2.0",
        "QPL-1.0",
        "W3C",
        "WTFPL",
        "Zlib",
        "Zope",
        "open-source", "restricted", "unrestricted", "unknown"
    } = ();

    # This magic builds our hash of keys, with `1` as the value for each.
    @licenses{keys %licenses} = (1) x keys %licenses;

    return %licenses;
}

1;
