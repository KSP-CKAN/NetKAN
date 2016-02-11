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

    if (my $overrides = $metadata->{x_netkan_override}) {

        my $is_array = ref($overrides) eq "ARRAY";

        ok($is_array, "Netkan overrides require an array");

        # If we don't have an array, then skip this next part.
        $overrides = [] if not $is_array;

        foreach my $override (@$overrides) {
            ok(
                $override->{version},
                "$shortname - Netkan overrides require a version"
            );

            ok(
                $override->{delete} || $override->{override},
                "$shortname - Netkan overrides require a delete or override section"
            );
        }
    }

    my $spec_version = $metadata->{spec_version};
    ok(
        $spec_version =~ m/^1$|^v\d\.\d\d?$/, 
        "spec version must be 1 or in the 'vX.X' format"
    );

    foreach my $install (@{$metadata->{install}}) {
        if ($install->{install_to} =~ m{^GameData/}) {
            ok(
                compare_version($spec_version,"v1.2"),
                "$shortname - spec_version v1.2+ required for GameData with path."
            );
        }

        if ($install->{install_to} =~ m{^Ships/}) {
            ok(
                compare_version($spec_version,"v1.12"),
                "$shortname - spec_version v.12+ required to install to Ships/ with path."
            );
        }

        if ($install->{find}) {
            ok(
                compare_version($spec_version,"v1.4"),
                "$shortname - spec_version v1.4+ required for install with 'find'"
            );
        }
        if ($install->{find_regexp}) {
            ok(
                compare_version($spec_version,"v1.10"),
                "$shortname - spec_version v1.10+ required for install with 'find_regexp'"
            );
        }
    }
}

# 1.10 is < 1.2 our number comparisons don't work now :( 
# TODO: Do something better than this quick hack
sub compare_version {
  my ($spec_version, $min_version) = @_;

  $spec_version =~ s/v1\.([2|4])$/v1.0$1/;
  $min_version =~ s/v1\.([2|4])$/v1.0$1/;

  print "Spec: $spec_version, Min: $min_version\n";

  if ($spec_version ge $min_version) {
    return 1;
  } else {
    return 0;
  }
}

done_testing;
