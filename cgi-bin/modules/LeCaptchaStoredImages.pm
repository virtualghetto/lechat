=pod
-----BEGIN PGP SIGNED MESSAGE-----

/####################################################################
#                                                                   #
#   StoredImages - EXAMPLE CAPTCHA MODULE for LE CHAT 2.0           #
#                                                                   #
#   A pool of stored images is used and a temporary file written.   #
#   The temporary image will be loaded directly by the browser.     #
#   This approach will work with any limited server configuration.  #
#                                                                   #
#   You'll have to change the image set regularly in case you are   #
#   targeted by a persistent spammer, otherwise he can store every  #
#   image he gets with the solution done manually and then reuse    #
#   the solution if the same image reappears. If his bot gets in    #
#   often, it's time to change the image set again.                 #
#                                                                   #
#   Check out this site for the general concept:                    #
#   http://bumblebeeware.com/captcha/                               #
#   There are also some image sets available that you can use.      #
#                                                                   #
#   The path where the temporary images for display in the browser  #
#   are stored must be set in the LE CHAT superuser configuration.  #
#                                                                   #
#   For more difficult CAPTCHA images you should generate them on   #
#   a local machine in bulk and then replace them regularly on the  #
#   server. The file name must be the solution, the extension can   #
#   be gif, jpg, jpeg or png.                                       #
#   You can use generate.pl on a local Perl installation with all   #
#   needed libraries installed and any of the LeCaptcha-modules     #
#   for that, as long as the output is a single binary image and    #
#   the solution contains ASCII-letters and numbers only.           #
#                                                                   #
#   LeCaptchaStoredImages.pm - Last changed: 2018-01-04             #
#                                                                   #
####################################################################/
=cut

package LeCaptchaStoredImages;
use strict;
no warnings 'uninitialized';

###################################################################
# You may change the directory with the pool of premade images.   #
# Can be an absolute server-path or relative to this module file. #
# This directory must be inaccessible for the web-user!           #
###################################################################
my $imagesdir='./StoredImages/';
###################################################################

sub generate_challenge{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	my $tempfile=$CONFIG->{captchaimgdir}.'/CAPTCHA'.$^T.random_text(4,0..9);# random filename for temporary image to show
	create_directory($CONFIG->{captchaimgdir}) unless -d$CONFIG->{captchaimgdir};
	return $INT->{errfile}." (mkdir)" unless -d$CONFIG->{captchaimgdir};
	$CAPTCHA->{solution}=random_image($imagesdir,$tempfile,my$err);# select a premade stored captcha image
	return $INT->{errfile}." ($err)" if $err;
	$CAPTCHA->{tempdata}=$tempfile;
	return qq|<br><table><tr><td valign="middle"><img src="$tempfile" alt="CAPTCHA"></td><td valign="middle"><input type="text" name="answer" size="8" value=""></td></tr></table><br>|;
}

sub verify_response{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	unlink($CAPTCHA->{tempdata});# remove temporary image file
	return 1 if($CAPTCHA->{solution} eq $QUERY->{answer}[0]);
	delete_expired($CONFIG->{captchaimgdir},$CONFIG->{captchaexpire});# remove any old leftover temporary files
	return 0;
}

sub random_text{
	my $count=shift;
	my @chars=split('',join('',@_));
	my $string;
	$string.=$chars[rand@chars]for 1..$count;
	return $string;
}

sub random_image{
	my($imagesdir,$tempfile)=@_;
	$imagesdir=get_path($imagesdir);
	my @images;
	opendir(my$DIR,$imagesdir) or $_[2]='opendir' and return;
	while($_=readdir($DIR)){if($_=~/^(.*\.(?:gif|jpe?g|png))$/i){push@images,$1}}
	unless(@images){$_[2]='readdir' and return}
	my$random=$images[rand@images];
	my($solution,$extension)=$random=~/^(.*)(\.\w+)$/;
	$tempfile.=$extension;
	copy_file($imagesdir.'/'.$random,$tempfile) or $_[2]='copy' and return;
	$_[1]=$tempfile;
	return $solution;
}

sub copy_file{
	my($src,$dst)=@_;
	open(my$SRC,'<',$src) or return 0;binmode($SRC);
	open(my$DST,'>',$dst) or return 0;binmode($DST);
	while(read($SRC,my$chunk,65536)){print $DST $chunk}
	close($SRC) or return 0;
	close($DST) or return 0;
	return 1;
}

sub create_directory{
	my @dirs=split('/',$_[0]);my $dir='';
	while($_=shift@dirs){$dir.=$_;mkdir($dir,0711) unless -d$dir;$dir.='/'}
	chmod(0711,$_[0]);
}

sub delete_expired{
	my($imagesdir,$expire)=@_;
	opendir(my$DIR,$imagesdir) or return;
	while($_=readdir($DIR)){
		my($timestamp)=$_=~/^CAPTCHA(\d*?)\d{4}\./;
		if($timestamp and ($^T-$timestamp>60*$expire)){unlink($imagesdir.'/'.$_)}
	}
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

iQA/AwUBWk4T/Mr7q1ZyCqQiEQIx7wCgg2ydkpywtjL+b7uc5yt37CzweJYAoK7Q
oMCp0JSKRJ3D0h5GhI85RWNE
=yMbF
-----END PGP SIGNATURE-----
