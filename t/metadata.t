#!/usr/bin/perl
use v5.010;
use lib 't/lib';
use autodie;
use Test::Most;
use Test::NetKAN qw(netkan_files read_netkan licenses);

use Data::Dumper;

my %licenses = licenses();

my %files = netkan_files;

foreach my $shortname (sort keys %files) {
    my $metadata = read_netkan($files{$shortname});

    is(
        $metadata->{identifier},
        $shortname,
        "$shortname.netkan identifer should match filename"
    );

    my $mod_license = $metadata->{license} // "(none)";

    ok(
        $metadata->{x_netkan_license_ok} || $licenses{$mod_license},
        "$shortname license ($mod_license) should match spec. Set `x_netkan_license_ok` to supress."
    );

    ok(
        $metadata->{'$kref'} || $metadata->{'$vref'},
        "$shortname has no \$kref/\$vref field. It belongs in CKAN-meta"
    );
}

done_testing;
