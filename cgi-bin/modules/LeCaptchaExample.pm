=pod
-----BEGIN PGP SIGNED MESSAGE-----

/####################################################################
#                                                                   #
#   Example - EXAMPLE CAPTCHA MODULE for LE CHAT 2.0                #
#                                                                   #
#   This module is just here to show how the CAPTCHA interface for  #
#   LE CHAT works. Use it as a template for your own CAPTCHAs.      #
#   Also check out all the other available modules to learn how     #
#   things can be done.                                             #
#                                                                   #
#   How to create your own CAPTCHAs?                                #
#                                                                   #
#   Save this file as e.g. LeCaptchaNEWCAPTCHA.pm where             #
#   "NEWCAPTCHA" is the name you want to give your new CAPTCHA      #
#   module. Then edit the line in the script according to the       #
#   filename, so that it says:                                      #
#                                                                   #
#   package LeCaptchaNEWCAPTCHA;                                    #
#                                                                   #
#   Your new CAPTCHA module should then show up in the chat         #
#   configuration as "NEWCAPTCHA".                                  #
#                                                                   #
#   Essential subs, called from lechat.cgi:                         #
#                                                                   #
#   generate_challenge()   Create your CAPTCHA challenge here and   #
#                          return the HTML to display.              #
#                                                                   #
#   verify_response()      Check if the CAPTCHA was solved          #
#                          correctly and return true or false.      #
#                                                                   #
#   output_image()         Assemble a visual challenge here and     #
#                          print out the image data.                #
#                                                                   #
#   Check all the comments below for further explanations.          #
#                                                                   #
#   LeCaptchaExample.pm - Last changed: 2018-01-04                  #
#                                                                   #
####################################################################/
=cut

package LeCaptchaExample;# must be LeCaptchaXXXXX and filename must be LeCaptchaXXXXX.pm

use strict;
no warnings 'uninitialized';

#####################################################################
# Essential functions called from lechat.cgi:                       #
#####################################################################

sub generate_challenge{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	# Called from lechat.cgi as: eval('$html=$modname->generate_challenge(\%Q,\%C,\%K,\%I)');
	#
	# Current Queries and Config from lechat.cgi are available via
	# hash-references, e.g.: $QUERY->{session}[0] or $CONFIG->{captchaexpire}
	#
	# A new captchaid to keep track will be automatically added to the html by lechat.cgi
	# <IMAGE> will be replaced by the correct URL with same captchaid to show a dynamic image
	# with output_image() below.
	# You'll have to provide an input field yourself, for the user to enter the solution!
	#
	# You can use $CAPTCHA->{tempdata} for any needed data besides the solution.
	# It can also be used to pass data from a wrong response to the next challenge.

	$CAPTCHA->{solution}=random_text(4,0..9);
	my $html='<br><br>Example-CAPTCHA<br><br>Type this: '.$CAPTCHA->{solution}.' '.text('answer','','3');
	if($CAPTCHA->{tempdata} eq 'WRONG'){
		$html='<br><br><i>Wrong answer, please try again!</i>'.$html ;
	}
	return $html;
}

sub verify_response{  
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	# Called from lechat.cgi as: eval('$success=$modname->verify_response(\%Q,\%C,\%K,\%I)');
	#
	# Current Queries and Config from lechat.cgi are available via hash-references,
	# e.g.: $QUERY->{session}[0] or $CONFIG->{captchaexpire}
	#
	# The captchaid is always available as $QUERY->{captchaid}[0] or $CAPTCHA->{captchaid}
	# The CAPTCHA solution is available as $CAPTCHA->{solution}
	# $QUERY->{answer}[0] contains the user input, if you named the input field "answer".
	#
	# Simply return 1 if the CAPTCHA is solved and the chat session should start,
	# or return 0 if it's wrong and another CAPTCHA should be shown.
	#
	# To feed back any data to the next challenge, you can use $CAPTCHA->{tempdata}

	my $success=0;
	if($CAPTCHA->{solution} eq $QUERY->{answer}[0]){
		$success=1
	}else{
		$CAPTCHA->{tempdata}='WRONG';
	}
	return $success;
}

sub output_image{
	my($MODULE,$QUERY,$CONFIG,$CAPTCHA,$INT)=@_;
	# Called from lechat.cgi as: eval('$modname->output_image(\%Q,\%C,\%K,\%I)');
	#
	# Not all servers support binary content-types from CGI-output, so this may not work!
	# You can store temporary image files instead, see LeCaptchaStoredImages.pm, or you
	# could use the Data URI scheme and embed base64-encoded images directly in the HTML.
	#
	# Current Queries and Config from lechat.cgi are available via hash-references,
	# e.g.: $QUERY->{session}[0] or $CONFIG->{captchaexpire}
	#
	# The captchaid is always available as $QUERY->{captchaid}[0] or $CAPTCHA->{captchaid}
	# The CAPTCHA solution is available as $CAPTCHA->{solution}
	#
	# Attention! Changes to any variables won't get saved. The solution is fixed already.

	print "Pragma: no-cache\nExpires: 0\n";
	binmode(STDOUT);
	# Output image data here and include headers, e.g.:
	# print "Content-Type: image/gif\nContent-Length: 165\n\n";
	print_error_image('Testing');
}

#####################################################################
# Helper-functions you may find useful for your own CAPTCHAs:       #
#####################################################################

sub random_text{
	# Takes a number for the length and then any lists or strings with characters.
	# Returns a string with the given length and random characters from the given parameters.
	#
	# Example: $CAPTCHA->{solution}=random_text( 5 , 0..9 , 'A'..'Z' , "+-*" );

	my $count=shift;
	my @chars=split('',join('',@_));
	my $string;
	$string.=$chars[rand@chars]for 1..$count;
	return $string;
}

sub print_error_image{
	# If there's an error happening in output_image(), e.g. a file cannot be opened,
	# you can display this error image and attach the error message to the headers.
	# A user won't see the message, but if you monitor the headers with Proxomitron
	# or another tool, you can use it for debugging.
	
	if(@_){my$err="@_";$err=~s/[\r\n]/ /g;print "X-LeCaptcha-Error: $err\n"}
	print "Content-Type: image/gif\nContent-Length: 147\n\n";
	binmode(STDOUT);
	# hex encoded little error-gif:
	print pack('H*','47494638376110001000b30000000000999999ff0000ffffff0000000000000000000000000000000000000000000000000000000000000000000000002c000000001000100000044850884147a858eac0c1cdd2a0016415001a158cdfb9a9a874b932464f6b88c15abac33989e7d789c9863652eff8e1098327dbc813448a84a4e1eb2ac89266a9a9d7bbe498cf9c6b04003b');
}

sub textarea{# name, value, columns, rows
	# Provides a textarea input box.
	qq|<textarea name="$_[0]" rows="|.($_[3]|'4').qq|" cols="|.($_[2]|'40').qq|" wrap="off">$_[1]</textarea></td></tr>|;
}
sub text{# name, value, size
	# Provides a simple text input field.
	qq|<input type="text" name="$_[0]" size="|.($_[2]?$_[2]:'20').qq|" value="$_[1]">|;
}

sub get_path{
	# Returns a proper working file path for paths relative to this module file.
	# Useful if you need to store data files next to your module file, since the
	# current working directory is always that of the cgi file.
	#
	# Example: get_path('./images') would return the correct path to the images
	# directory if it's stored next to the module file.
	#
	# Absolute paths won't get changed and will still work.

	my$dir="@_";
	unless($dir=~m~^([/\\]|[a-z]:[\\/])~i){# absolute path already?
		my($mdir)=__FILE__=~m{^(.+[/\\])};# directory where this module resides
		$dir=$mdir.'/'.$dir;
		$dir=~s~[/\\]\.[/\\]~/~g;
		$dir=~s~[/\\]+~/~g;
	}
	$dir=~s~[\\/]+$~~;
	return $dir;
}

#####################################################################
1;
__END__

-----BEGIN PGP SIGNATURE-----

iQA/AwUBWk4RjMr7q1ZyCqQiEQIkgACg8A43/D1GcXusOgrWuRYixB0UoisAoPzT
U96TZbKTW2dqXYyuzw1tSq5r
=6OV/
-----END PGP SIGNATURE-----
