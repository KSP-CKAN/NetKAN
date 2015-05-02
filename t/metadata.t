#!/usr/bin/perl
use v5.010;
use lib 't/lib';
use autodie;
use strict;
use Test::Most;
use Test::NetKAN qw(netkan_files read_netkan licenses);

use Data::Dumper;

my $ident_qr = qr{^[A-Za-z][A-Z-a-z0-9-]*$};

my %licenses = licenses();

my %files = netkan_files;

foreach my $shortname (sort keys %files) {
    my $metadata = read_netkan($files{$shortname});

    is(
        $metadata->{identifier},
        $shortname,
        "$shortname.netkan identifer should match filename"
    );

    like(
        $metadata->{identifier},
        $ident_qr,
        "$shortname: CKAN identifers must consist only of letters, numbers, and dashes, and must start with a letter."
    );

    foreach my $relation (qw(depends recommends suggests conflicts)) {
        foreach my $mod (@{$metadata->{$relation}}) {
            like(
                $mod->{name},
                $ident_qr,
                "$shortname: $mod->{name} in $relation is not a valid CKAN identifier"
            );
        }
    }

    my $mod_license = $metadata->{license} // "(none)";

    ok(
        $metadata->{x_netkan_license_ok} || $licenses{$mod_license},
        "$shortname license ($mod_license) should match spec. Set `x_netkan_license_ok` to supress."
    );

    ok(
        $metadata->{'$kref'} || $metadata->{'$vref'},
        "$shortname has no \$kref/\$vref field. It belongs in CKAN-meta"
    );

    my $spec_version = $metadata->{spec_version};
    foreach my $install (@{$metadata->{install}}) {
        if ($install->{install_to} =~ m{^GameData/}) {
            ok(
                $spec_version ge "v1.2",
                "$shortname - spec_version v1.2+ required for GameData with path."
            );
        }

        if ($install->{find}) {
            ok(
                $spec_version ge "v1.4",
                "$shortname - spec_version v1.4+ required for install with 'find'"
            );
        }
    }
}

done_testing;
