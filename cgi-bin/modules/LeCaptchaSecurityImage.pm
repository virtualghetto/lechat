=pod
-----BEGIN PGP SIGNED MESSAGE-----

/####################################################################
#                                                                   #
#   SecurityImage - EXAMPLE CAPTCHA MODULE for LE CHAT 2.0          #
#                                                                   #
#   Simple usage of GD::SecurityImage                               #
#                                                                   #
#   Perl module prerequisites: GD, GD::SecurityImage                #
#                                                                   #
#   For playing with the parameters check out the documentation:    #
#   https://metacpan.org/pod/GD::SecurityImage                      #
#                                                                   #
#   For free fancy TTF-fonts check out this site:                   #
#   http://www.1001fonts.com/                                       #
#                                                                   #
#   Don't overdo it with crazy fonts, you don't want to annoy       #
#   legitimate users too much. Humans must be able to read it!      #
#                                                                   #
#   LeCaptchaSecurityImage.pm - Last changed: 2018-01-04            #
#                                                                   #
####################################################################/
=cut

package LeCaptchaSecurityImage;
use strict;
no warnings 'uninitialized';

use GD::SecurityImage;

#####################################################################
# Parameters you can change to your liking:                         #
# See: https://metacpan.org/pod/GD::SecurityImage                   #
#####################################################################

# Directory with ttf files, one of the fonts is randomly chosen.
# You can try to give the path relative to this module file. 
# If the ttf won't show, you should specify the absolute path.
my $ttfdir='./fonts/';

# method new:
my %new=(
	width      => 300,
	height     => 150,
	ptsize     => 36,
	lines      => rand(4),
	bgcolor    => '#000000',
	send_ctobg => 0,
	frame      => 0,
	scramble   => 0,
	angle      => (345+int(rand(30)))%360,
	thickness  => 2,
	rndmax     => 1,
);

# method create:
my $style      = 'blank'  ;# default rect box circle ellipse ec blank
my $text_color = '#FFAAAA';
my $line_color = '#FFAAAA';

# method particle:
my $density = 3000;
my $maxdots = 2;

# method info_text:
my %info_text=(
	x      => 'left',
	y      => 'up',
	strip  => 0,
	gd     => 0,
	ptsize => 20,
	color  => '#EEEEFF',
	scolor => '#555555',
	text   => 'Type the text:',
);

#####################################################################

sub generate_challenge{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	my $html;
	$CAPTCHA->{solution}=random_text(4+int(rand(3)),'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789');
	$html=qq|<br><img src="<IMAGE>" alt="CAPTCHA"></td></tr><tr><td valign="middle" align="center"><br><input type="text" name="answer" size="8" value="">|;
	return $html;
}

sub verify_response{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	return 1 if($CAPTCHA->{solution} eq $QUERY->{answer}[0]);
	return 0
}

sub output_image{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	my @fonts;
	$ttfdir=get_path($ttfdir);
	if(opendir(my$DIR,$ttfdir)){while(my$f=readdir($DIR)){if($f=~/\.ttf$/i){push@fonts,$f}}}
	my $font=$fonts[rand@fonts];
	my $image=GD::SecurityImage->new(%new,font=>"$ttfdir/$font",gd_font=>$font?'':'Giant',rndmax=>1);
	$image->random($CAPTCHA->{solution});
	$image->create($font?'ttf':'normal',$style,$text_color,$line_color);
	$image->particle($density,$maxdots);
	$image->info_text(%info_text);
	my($data,$type,$random)=$image->out;
	print "Pragma: no-cache\nExpires: 0\nContent-Type: image/$type\n\n";
	binmode STDOUT;
	print $data;
}

sub random_text{
	my $count=shift;
	my @chars=split('',join('',@_));
	my $string;
	$string.=$chars[rand@chars]for 1..$count;
	return $string;
}

sub get_path{
	my$dir="@_";
	unless($dir=~m~^([/\\]|[a-z]:[\\/])~i){
		my($mdir)=__FILE__=~m{^(.+[/\\])};
		$dir=$mdir.'/'.$dir;
		$dir=~s~[/\\]\.[/\\]~/~g;
		$dir=~s~[/\\]+~/~g;
	}
	$dir=~s~[\\/]+$~~;
	return $dir;
}

1;
__END__

-----BEGIN PGP SIGNATURE-----

iQA/AwUBWk4U38r7q1ZyCqQiEQLVGACeLoo4NvA9VSYILDc+Bcjz91IWB8IAoICD
FR5X7PbxUPr6JRDH7K6b1Gn+
=Ioxo
-----END PGP SIGNATURE-----
