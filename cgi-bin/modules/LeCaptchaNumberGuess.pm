=pod
-----BEGIN PGP SIGNED MESSAGE-----

/####################################################################
#                                                                   #
#    NumberGuess - EXAMPLE CAPTCHA MODULE for LE CHAT 2.0           #
#                                                                   #
#    Guess a random number as a primitive CAPTCHA module.           #
#                                                                   #
#    By definition it's not really a "CAPTCHA", since it doesn't    #
#    stop bots, but it may encourage participation of lurkers who   #
#    time out often in the chat. ;)                                 #
#                                                                   #
#    LeCaptchaNumberGuess.pm - Last changed: 2018-01-04             #
#                                                                   #
####################################################################/
=cut

package LeCaptchaNumberGuess;
use strict;
no warnings 'uninitialized';

sub generate_challenge{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	my $html='<i>Sorry, something went wrong.</i><br>';
	if($CAPTCHA->{solution}<1 or $CAPTCHA->{solution}>100){# empty, or remnant of other CAPTCHA module if it was switched
		$CAPTCHA->{solution}=1+int(rand(100));
		$html='Your guess: '.text('answer','',"3");
	}elsif($CAPTCHA->{tempdata}eq'-'){
		$html="<i>Come on, you didn't even try!</i><br><br>Your guess: ".text('answer','',"3");
	}elsif($CAPTCHA->{tempdata}eq'?'){
		$html="<i>Try a proper number!</i><br><br>Your guess: ".text('answer','',"3");
	}elsif($CAPTCHA->{tempdata}==$CAPTCHA->{solution}){
		$html="$CAPTCHA->{tempdata} is correct, come in!";
		$CAPTCHA->{tempdata}='OK';
	}elsif($CAPTCHA->{tempdata}<$CAPTCHA->{solution}){
		$html="<i>$CAPTCHA->{tempdata} is too low, try again!</i><br><br>Your guess: ".text('answer','',"3");
	}elsif($CAPTCHA->{tempdata}>$CAPTCHA->{solution}){
		$html="<i>$CAPTCHA->{tempdata} is too high, try again!</i><br><br>Your guess: ".text('answer','',"3");
	}
	return "<br><br><b>I made up a number between 1 and 100 and you must guess it!</b><br><br>$html<br><br>";
}

sub verify_response{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	return 1 if($CAPTCHA->{tempdata}eq'OK');
	$CAPTCHA->{tempdata}=$QUERY->{answer}[0];
	if($CAPTCHA->{tempdata}eq''){$CAPTCHA->{tempdata}='-'}
	elsif($CAPTCHA->{tempdata}=~/\D/){$CAPTCHA->{tempdata}='?'}
	return 0;
}

sub text{qq|<input type="text" name="$_[0]" size="|.($_[2]?$_[2]:'20').qq|" value="$_[1]">|}

1;
__END__

-----BEGIN PGP SIGNATURE-----

iQA/AwUBWk4WIcr7q1ZyCqQiEQK8kQCfet1/kHdj8tGC4WskZpzIhWklEUYAoOWA
bW/yUuITjGOiEkyKWEJraXcb
=MQlH
-----END PGP SIGNATURE-----
