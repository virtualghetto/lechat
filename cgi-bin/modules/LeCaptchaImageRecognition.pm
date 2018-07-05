=pod
-----BEGIN PGP SIGNED MESSAGE-----

/####################################################################
#                                                                   #
#   ImageRecognition - EXAMPLE CAPTCHA MODULE for LE CHAT 2.0       #
#                                                                   #
#   Implementation of a "Click all the images with ..."-CAPTCHA     #
#   that you may have seen all over the internet.                   #
#                                                                   #
#   Use your own funny images here, maybe even related to your      #
#   chat room discussion topics, and people may actually enjoy      #
#   solving that CAPTCHA. Cat pics e.g. are always fine! ;)         #
#   Make sure you change the image sets regularly if you get        #
#   attacked by bots.                                               #
#                                                                   #
#   To easily create uniform images in bulk, from directories on    #
#   your disk, you can use e.g. the IrfanView Thumbnails program.   #
#   "File" -> "Save selected thumbs as single images..."            #
#                                                                   #
#   LeCaptchaImageRecognition.pm - Last changed: 2018-01-04         #
#                                                                   #
####################################################################/
=cut

package LeCaptchaImageRecognition;
use strict;
no warnings 'uninitialized';

#####################################################################
# Adapt these variables to your specific images to recognise:       #
#####################################################################
my $task = 'Check only the pictures with [something] in them!';
my $dir0 = 'ImageRecognition/false/'    ;# directory with false pics
my $dir1 = 'ImageRecognition/true/'     ;# directory with true pics
my $cols = 3                            ;# columns of pictures to use
my $rows = 2                            ;# rows of pictures to use
my $picx = 200                          ;# picture display width
my $picy = 200                          ;# picture display height
#####################################################################

sub generate_challenge{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	my @pics;my $err;
	my @pic0=image_list($dir0,$err);return $INT->{errfile}." ($err)" if$err;
	my @pic1=image_list($dir1,$err);return $INT->{errfile}." ($err)" if$err;
	my $html=qq|<br><br><table border="1" bgcolor="#$CONFIG->{colbg}"><tr><th colspan="$cols" align="center"><font color="#$CONFIG->{coltxt}"><b>$task</b></font></th></tr><tr>|;
	$CAPTCHA->{solution}=int(rand(2**($cols*$rows)-1)+1);# as a binary every bit is a true or false picture
	for(my$i=1;$i<=$cols*$rows;$i++){
		$pics[$i-1]=((2**($i-1))&int($CAPTCHA->{solution}))?$pic1[rand@pic1]:$pic0[rand@pic0];
		$html.=qq|<td align="right" valign="bottom" width="$picx" height="$picy"><div style="position:relative"><label for="x$i" id="l$i"><img width="$picx" height="$picy" src="<IMAGE>&amp;picture=$i" alt="[?]"></label><div style="position:absolute;bottom:2px;right:2px;"><input type="checkbox" name="x$i" value="x$i" id="x$i"></div></div></td>|;
		$html.='</tr><tr>' if($i%$cols==0&&$i<$cols*$rows);
	}
	$html.=q|</tr></table><br>|;
	$CAPTCHA->{tempdata}=join('<>',@pics);
	return $html;
}

sub verify_response{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	my $answer=0;
	for(my$i=1;$i<=$cols*$rows;$i++){$answer+=2**($i-1)if($QUERY->{"x$i"}[0])}
	return 1 if($CAPTCHA->{solution}==$answer);
	return 0;
}

sub output_image{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	my @pics=split('<>',$CAPTCHA->{tempdata});
	my $pic=$pics[$QUERY->{picture}[0]-1];
	my($type)=$pic=~/\.(gif|jpe?g|png)$/;$type=~s/jpg/jpeg/;
	if(open(my$FH,'<',$pic)){
		print "Pragma: no-cache\nExpires: 0\nContent-Type: image/$type\n\n";
		binmode($FH);
		binmode(STDOUT);
		while(read($FH,my$chunk,65536)){print $chunk}
		close($FH);
	}else{print_error_image($!)}
}

sub image_list{
	my $dir=get_path($_[0]);
	my @images;
	opendir(my$DH,$dir) or $_[1]='opendir' and return;
	while($_=readdir($DH)){if($_=~/^(.*\.(?:gif|jpe?g|png))$/i){push@images,"$dir/$1"}}
	unless(@images){$_[1]='readdir' and return}
	return @images;
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

sub print_error_image{
	if(@_){my$err="@_";$err=~s/[\r\n]/ /g;print "X-LeCaptcha-Error: $err\n"}
	print "Content-Type: image/gif\nContent-Length: 147\n\n";
	binmode(STDOUT);
	print pack('H*','47494638376110001000b30000000000999999ff0000ffffff0000000000000000000000000000000000000000000000000000000000000000000000002c000000001000100000044850884147a858eac0c1cdd2a0016415001a158cdfb9a9a874b932464f6b88c15abac33989e7d789c9863652eff8e1098327dbc813448a84a4e1eb2ac89266a9a9d7bbe498cf9c6b04003b');
}

1;
__END__

-----BEGIN PGP SIGNATURE-----

iQA/AwUBWk4PM8r7q1ZyCqQiEQIqFgCgmN7aWllQ4PMtJLvrOfhUYdcBEXoAoNv3
GqJyXBHw0/RCiMFyYGFpTkOi
=memI
-----END PGP SIGNATURE-----
