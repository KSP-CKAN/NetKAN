#!/usr/bin/perl -w
use 5.010;
use strict;
use warnings;
use autodie qw(:all);
use Test::More;
use IPC::System::Simple qw(capture $EXITVAL);
use WWW::Mechanize;

my $pr_branch = $ENV{TRAVIS_PULL_REQUEST};
my $netkan = "./netkan.exe";

if (! $pr_branch or $pr_branch eq "false") {
    plan skip_all => "Not a travis pull request";
}

if (! -x $netkan) {

    # If we don't already have a netkan executable, then go download the latest.
    # This includes unstable netkan.exe builds, as submissions may reference
    # experimental features.

    my $agent = WWW::Mechanize->new( agent => "NetKAN travis testing" );
    $agent->get("https://github.com/KSP-CKAN/CKAN/releases");
    $agent->follow_link(text => 'netkan.exe');

    open(my $fh, '>', $netkan);
    binmode($fh);
    print {$fh} $agent->content;
    close($fh);
    chmod(0755, $netkan);
}

# FETCH_HEAD^ should always be the branch we're merging into.
my @changed_files = capture("git diff --name-only FETCH_HEAD^");
chomp(@changed_files);

# Walk through our changed files. If any of them mention KS, then
# run netkan over them. (We have @sircmpwn's permission to make KS
# downloads during CI testing.)

my $tests_ran = 0;

foreach my $file (@changed_files) {
    if (is_testable_file($file)) {
        netkan_validate($file);
        $tests_ran++;
    }
}

if ($tests_ran == 0) {
    plan skip_all => "No .netkan files were changed";
}

done_testing;

# Returns true if this is a file we want to test.
# We test both KS and github releases for now.
sub is_testable_file {
    my ($file) = @_;

    # Not a netkan file? Not something we want to test.
    return 0 if ($file !~ m{\.netkan$});

    local $/;   # Slurp mode.

    open(my $fh, '<', $file);
    my $content = <$fh>;
    close($fh);

    return $content =~ m{#/ckan/(?:kerbalstuff|github)};
}

# Simply checks to see if netkan.exe runs without errors on this file
sub netkan_validate {
    my ($file) = @_;

    my $netkan_output;

    eval { $netkan_output = capture([-1], $netkan, $file) };

    # If there was a failure running netkan.exe, report it
    if ($@) {
        ok(0, $file);
        diag "Something unexpected happened: $@";
    }
    # If we didn't get a validation pass, report that too.
    elsif ($EXITVAL != 0) { 
        ok(0, $file);
        diag "$netkan_output"
    }
    # Otherwise huzzah, the changes look good.
    else {
        ok(1, $file);
    }
}
