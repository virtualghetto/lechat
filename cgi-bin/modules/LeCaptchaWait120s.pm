=pod
-----BEGIN PGP SIGNED MESSAGE-----

/####################################################################
#                                                                   #
#    Wait120s - EXAMPLE CAPTCHA MODULE for LE CHAT 2.0              #
#                                                                   #
#    Simple 120s waiting time as a primitive CAPTCHA module.        #
#                                                                   #
#    By definition it's not really a "CAPTCHA", since it doesn't    #
#    stop bots, but it may encourage participation of lurkers who   #
#    time out often in the chat. ;)                                 #
#                                                                   #
#    LeCaptchaWait120s.pm - Last changed: 2018-01-04                #
#                                                                   #
####################################################################/  
=cut

package LeCaptchaWait120s;
use strict;
no warnings 'uninitialized';

sub generate_challenge{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	if($CAPTCHA->{tempdata}>0 and $CAPTCHA->{tempdata}<=120){# explicit check in case module was switched
		return '<br><br><b>You still have to wait '.$CAPTCHA->{tempdata}.' seconds before you can continue!</b><br><br>';
	}else{
		$CAPTCHA->{solution}=$^T+120;
		return '<br><br><b>You have to wait 120 seconds before you can continue!</b><br><br>';
	}
}

sub verify_response{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	$CAPTCHA->{tempdata}=$CAPTCHA->{solution}-$^T;# send back remaining time if continue-button is clicked early
	return ($CAPTCHA->{tempdata}<2)?1:0;
}

1;
__END__

-----BEGIN PGP SIGNATURE-----

iQA/AwUBWk4TOcr7q1ZyCqQiEQL6ZQCfc/1ERM4Y5JMHCoRk39IEN25xC3kAoLvn
vQkhCwPtJL1K31beLAE7kJAv
=4t3x
-----END PGP SIGNATURE-----
