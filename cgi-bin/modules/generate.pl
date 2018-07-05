#!/usr/bin/perl

=pod
-----BEGIN PGP SIGNED MESSAGE-----

/####################################################################
#                                                                   #
#   Bulk CAPTCHA-Images Generator for LE CHAT CAPTCHA-Modules       #
#                                                                   #
#   If your hosting doesn't support graphics libraries or binary    #
#   output from CGI scripts, you can still use static image files   #
#   with the "LeCaptchaStoredImages.pm" CAPTCHA module.             #
#                                                                   #
#   Use this script here with existing CAPTCHA-modules, on a local  #
#   machine where all modules are working, to generate CAPTCHA-     #
#   images in bulk. Upload those pictures then to your server and   #
#   point the StoredImages module to your premade image files.      #
#                                                                   #
#   Requirements/Limitations:                                       #
#                                                                   #
#   -Output of the used CAPTCHA-module must be a single picture.    #
#   -CAPTCHA-solution can only contain ASCII-letters and numbers.   #
#   -Solution must be unambigious and can't have variations.        #
#                                                                   #
#   You can run generate.pl either from a commandline or as a CGI-  #
#   script on a (local) webserver to generate your CAPTCHA-images.  #
#                                                                   #
#   generate.pl - Last changed: 2018-01-04                          #
#                                                                   #
####################################################################/
=cut

use strict;
use warnings;
no warnings 'uninitialized';

######################################################################
# Usage example from commandline: 
# perl -x -S C:\Scripts\generate.pl SecurityImage 10000 "./new pics"
######################################################################
my($module,$count,$directory)=@ARGV;

######################################################################
# Default values if none given in commandline or script is run as CGI:
######################################################################
$module||='SecurityImage';
$count||=1000;
$directory||='./generated';

######################################################################
my$modfile="./LeCaptcha$module.pm";
my$modname='LeCaptcha'.$module;
require $modfile;

print "Content-Type: text/plain\n\n" if $ENV{REMOTE_ADDR};
print '-'x79,"\n";
print "Generate CAPTCHA images in bulk.\n";
print '-'x79,"\n";
print "Module    : $module\n";
print "Count     : $count\n";
print "Directory : $directory\n";
print '-'x79,"\n";
my $faults=0;
my $files=0;
for(1..$count){
	last if $faults>=1000;# prevent endless loops
	my%Q;my%C;my%I;my%captcha;
	my$html=$modname->generate_challenge(\%Q,\%C,\%captcha,\%I);
	last unless $html=~/<IMAGE>/;
	$faults++ and redo if $captcha{solution}=~/[^a-zA-Z0-9]/;# don't accept special characters
	# capture image data in $image
	my $image='';
	open(my$MH,'>',\$image) or die $!;
	my $stdout=select $MH;
	$modname->output_image(\%Q,\%C,\%captcha,\%I);
	select $stdout;
	close($MH);
	# save as an image file
	my($header,$data)=$image=~/^([\w\W]+?\r?\n)\r?\n([\w\W]+)$/;
	my($type)=$header=~m{Content-Type:\s*image/(\w+)}i;$type||='unknown';
	my$filename="$directory/$captcha{solution}.$type";
	$faults++ and redo if -e$filename;# file exists already
	open(my$FH,'>',$filename) or die $!;
	binmode($FH);
	print $FH $data;
	close($FH);
	$files++;
	print '. ';
}
print "\n",'-'x79,"\n";
print "$files images saved, $faults duplicates/errors ignored.\n";
my$dummy=<STDIN> unless $ENV{REMOTE_ADDR};
exit;

__END__

-----BEGIN PGP SIGNATURE-----

iQA/AwUBWk4SuMr7q1ZyCqQiEQJZ1gCeK+/8lNdNfDxf+mn1qlvTtuo/ns0AoPh5
S5Z3K6AfzXjMA+v1wTnNi+to
=SV87
-----END PGP SIGNATURE-----
