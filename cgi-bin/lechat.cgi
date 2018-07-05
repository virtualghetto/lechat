#!/usr/bin/perl

=pod
-----BEGIN PGP SIGNED MESSAGE-----

/####################################################################
#                                                                   #
#    #      #####        ####  #   #   ###   #####      /\_/\       #
#    #      #           #      #   #  #   #    #       ( o.o )      #
#    #      ###         #      #####  #####    #        > ^ <       #
#    #      #           #      #   #  #   #    #        v2.0        #
#    #####  #####        ####  #   #  #   #    #      2018-01-05    #
#                                                                   #
#  Homepage: http://4fvfamdpoulu2nms.onion/lechat/                  #
#                                                                   #
#  Upload this script file into your cgi-bin directory and make it  #
#  executable.  If you have  language data or backups  you want to  #
#  restore initially,  you can copy that all into a textfile named  #
#  "lechat.txt" and put it next to your script file on the server.  #
#  Then call the script in your browser with parameter like this:   #
#                                                                   #
#  http://(server)/(cgi-path)/(script-name).cgi?action=setup        #
#                                                                   #
#  All further installation settings can be made from there then.   #
#  The (optional) CAPTCHA-modules have to be installed separately.  #
#  For more information, help and updates, check the homepage!      #
#                                                                   #
#  If you add your own cool features and want to share with others, #
#  feel free,  but please  modify at least the version tag and add  #
#  your name to it, so it is clear that it is not my original code  #
#  anymore.  If you send  me a copy of your edited script, I might  #
#  use some of your ideas in future versions. Thank you!            #
#                                                                   #
#  If you make translations and want to share them, please send me  #
#  a copy of the backup data for my website, thanks!  All text can  #
#  be edited conveniently as superuser on the setup page.           #
#                                                                   #
#  I wrote the script from scratch and all the code is my own, but  #
#  as you may notice,  I took some ideas  from other scripts  that  #
#  are out there. Special thanks to all the coders who built a lot  #
#  on v1.14, I've  implemented  some of your good ideas as well by  #
#  now. Bug reports and more feedback are always very welcome!      #
#                                                                   #
#  The "LE" in the name  you can take as  "Lucky Eddie", or  since  #
#  the script originally was  meant to be lean  and easy on server  #
#  resources, as "Light Edition".  It may even be the  french word  #
#  for "the" if you  prefer.  Translated  from  french to english,  #
#  "le chat" actually means: "the cat".                             #
#                                                                   #
#  Other than that, enjoy! ;)                                       #
#                                                                   #
#  Lucky Eddie                                                      #
#                                                                   #
####################################################################/

=cut

use strict;
use Fcntl qw(:DEFAULT :flock);
no warnings 'uninitialized';# those really make no sense with cgi

######################################################################
# Data directory. Change this if the setup shows it as vulnerable or
# protect it in your server configuration (e.g. with a .htaccess)!
######################################################################
my $datadir='./lcdat';

######################################################################
# If you do your own coding, please change these tags appropriately,
# by adding your nickname to the version or something like that.
######################################################################
my($version,$lastchanged)=('v2.0','2018-01-05');

######################################################################
# Uncomment the following line for debugging/developing only:
######################################################################
#use CGI::Carp 'fatalsToBrowser'; print "Content-Type: text/html\n";

######################################################################
# No need to change anything below. Always use: *.cgi?action=setup
######################################################################
my($S,%Q)=(&GetScript,&GetQuery,&GetParam);
my %T;# Test flags
my %U;# User data
my %P;# Present users in room (nick=>[hex,status,style])
my %A;# All members in file (nick=>[hex,status,style])
my @M;# Members: display names
my @G;# Guests: display names
my @S;# Staff: display names
my %F;# Fonts
my %I;# Internal texts and error messages
my %L;# Language editing
my %C;# Configuration
my %H;# HTML-stuff
my %K;# KAPUTCHA err.. CAPTCHA ;)
my %D;# Directories for modules and shared members file
use constant{
# unified user status levels:
	DEL=>-4,# delete from members file
	ACD=>-3,# access denied
	KCK=>-2,# kicked from room
	WND=>-1,# waiting newcomer denied
	UNK=> 0,# unknown/timeout
	NEW=> 1,# unknown nick wants to login
	WNW=> 2,# waiting newcomer waiting
	WNA=> 3,# waiting newcomer accepted
	GST=> 4,# guest
	REG=> 5,# registered user
	MOD=> 6,# moderator
	ADM=> 7,# regular administrator
	MAD=> 8,# main administrator
	SUP=> 9,# superuser
	SYS=>10,# system
# guest access settings:
	FBD=>0,# always forbid
	APP=>1,# approval needed
	STP=>2,# staff presense needed
	ALL=>3,# always allow
# chat access settings:
	SUS=>0,# suspended
	ENA=>1,# enabled
	STA=>2,# staff only
	LNK=>3,# link redirection only
};
load_config();

######################################################################
# main program: decide what to do based on queries
######################################################################

if($Q{action}[0]eq'setup'){
	send_init()if!-e filepath('admin');
	send_alogin()if valid_admin($Q{nick}[0],$Q{pass}[0],$Q{hexpass}[0])<MAD;
	if($Q{do}[0]eq'config'){
		set_config();
		save_config();
	}elsif($Q{do}[0]eq'chataccess'){ 
		set_chat_access($Q{chatset}[0]);
	}elsif($Q{do}[0]eq'backup'){
		$I{backdat}=get_backup($Q{what}[0]);
	}elsif($Q{do}[0]eq'restore'){
		$I{backdat}=get_restore_results();
	}elsif($Q{do}[0]eq'directories'&&$U{status}==SUP){
		set_directories();
		save_directories();
	}elsif($Q{do}[0]eq'mainadmin'&&$U{status}==SUP){
		send_setup(change_admin_status());
	}elsif($Q{do}[0]eq'resetlanguage'&&$U{status}==SUP){
		delete_file('language');
		load_config();
	}
	send_setup();
}
elsif($Q{action}[0]eq'init'&&!-e filepath('admin')){
	init_chat();
}
elsif($Q{action}[0]eq'language'){
	send_alogin()if!valid_admin($Q{nick}[0],$Q{pass}[0],$Q{hexpass}[0])==SUP;
	save_langedit()if$Q{do}[0]eq'save';
	$I{backdat}=get_restore_results('langedit')if$Q{do}[0]eq'restore';
	load_langedit();
	$I{backdat}=get_backup('langedit')if$Q{do}[0]eq'backup';
	send_language();
}
elsif($T{access}==SUS){
	send_suspended();
}
elsif($Q{action}[0]eq'redirect'){
	send_redirect($Q{url}[0]);
}
elsif($T{access}==LNK){
	send_suspended();
}
elsif($Q{action}[0]eq'captcha'){
	send_captcha_image();
}
elsif($Q{action}[0]eq'wait'){
	check_waiting_session();
	send_waiting_room();
}
elsif($Q{action}[0]eq'splash'){
	if(captcha_verified()){
		update_splash_session(1);
		send_waiting_room()if$U{status}==WNW;
		create_chatroom_session();
	}else{
		update_splash_session(0);
		send_splash_screen();
	}
}
elsif($Q{action}[0]eq'view'){
	check_session();
	send_messages();
}
elsif($Q{action}[0]eq'post'){
	if($Q{message}[0]=~/^\s*$/){
		check_session()
	}
	else{
		update_session();
		add_user_message()unless$U{filtered}==3;
		if($U{filtered}==2||$U{filtered}==3){# kickfilter
			if($U{status}<MOD){
				del_all_messages($U{nickname})if$U{filtered}==3;# purge
				kick_chatter($U{nickname},$U{kickmessage});
			}else{
				$U{message}=$I{kickfilter};
				$U{message}.=" ($U{kickmessage})"if$U{kickmessage};
				add_staff_message();
			}
		}
	}
	send_post();
}
elsif($Q{action}[0]eq'delete'){
	check_session();
	send_del_confirm()if$Q{what}[0]eq'all';
	del_all_messages($U{nickname})if$Q{what}[0]eq'allok';
	del_last_message($U{nickname})if$Q{what}[0]eq'last';
	send_post();
}
elsif($Q{action}[0]eq'login'){
	begin_login();
}
elsif($Q{action}[0]eq'chat'){
	check_session();
	send_frameset();
}
elsif($Q{action}[0]eq'controls'){
	check_session();
	send_controls();
}
elsif($Q{action}[0]eq'profile'){
	if($Q{do}[0]eq'save'){save_profile()}else{check_session()}
	send_profile();
}
elsif($Q{action}[0]eq'entry'){
	check_session();
	send_entry();
}
elsif($Q{action}[0]eq'logout'){
	exit_session();
	send_logout();
}
elsif($Q{action}[0]eq'colours'){
	check_session();
	send_colours();
}
elsif($Q{action}[0]eq'help'){
	check_session();
	send_help();
}
elsif($Q{action}[0]eq'admin'){
	check_session();
	send_login() unless $U{status}>=MOD;
	if($Q{do}[0]eq'clean'){
		send_choose_messages() if $Q{what}[0]eq'choose';
		clean_selected() if $Q{what}[0]eq'selected';
		clean_room() if $Q{what}[0]eq'room';
		send_messages();
	}
	elsif($Q{do}[0]eq'kick'){
		send_admin() if $Q{name}[0]eq'';
		unless(kick_chatter(hd($Q{name}[0]),$Q{kickmessage}[0])){
			send_admin($I{errcantkick});
		}
		del_all_messages(hd($Q{name}[0])) if $Q{what}[0]eq'purge';
		check_session();
		send_messages();
	}
	elsif($Q{do}[0]eq'logout'){
		send_admin() if $Q{name}[0]eq'';
		unless(logout_chatter(hd($Q{name}[0]))){
			send_admin($I{errcantlogout}); 
		}
		check_session();
		send_messages();
	}
	elsif($Q{do}[0]eq'sessions'){
		send_sessions();
	}
	elsif($Q{do}[0]eq'guests'){
		set_guests_access($Q{guestset}[0]);
	}
	elsif($Q{do}[0]eq'register'){
		register_guest();
		check_session();
		send_messages();
	}
	elsif($Q{do}[0]eq'status'){
		change_status();
	}
	elsif($Q{do}[0]eq'regnew'){
		register_new();
	}
	elsif($Q{do}[0]eq'newcomers'){
		edit_waiting_sessions($Q{what}[0]);
		send_waiting_admin();
	}
	send_admin();
}
read_sessions();
send_login();
exit;

######################################################################
# html output subs
######################################################################
# Warning! Be very careful, if you mess with my HTML/CSS anywhere! I #
# know some of my code  may look weird and redundant, but CSS sucks, #
# browsers are all buggy  and no two browsers  interpret  everything #
# the same. I tested  this chat extensively in a  variety of old and #
# new browsers, with and without CSS support and with different user #
# CSS settings.  I made sure it looks  and functions  acceptably for #
# everyone (hopefully).  It's not perfect though.  It looks  fine in #
# modern browsers  and it degrades well for browsers without any CSS #
# support.  Most problematic are  (older) browsers  with rudimentary #
# CSS capabilities. Those should still work well enough though. As a #
# rule of thumb,  be very conservative with  CSS tags and  don't use #
# all the  latest gimmicks!  You should  really test your code  with #
# more than just Tor Browser! Also remember that things must work in #
# noframes-mode as well, so check for that if you make changes!      #
######################################################################

sub print_headers{print "Content-Type: text/html; charset=$H{encoding}\nContent-Language: $I{languagecode}\nPragma: no-cache\nExpires: 0\nContent-Security-Policy: referrer no-referrer;\n"}
sub print_stylesheet{print '<style type="text/css"><!--',$C{cssglobal}?"\n$C{cssglobal}":'',($Q{noframes}[0]&&$C{csscontrols}&&$Q{action}[0]=~/^(chat|view|post|delete|profile|colours|help|admin)$/)?"\n$C{csscontrols}":'',$C{"css$_[0]"}?"\n".$C{"css$_[0]"}:'',$H{add_css}?"\n$H{add_css}":'',"\n--></style>\n";}
sub print_end{print_noframes(2);print $H{end_body},$H{end_html};exit}
sub form{qq|<form action="$S" |.($_[1]||$H{method}).($_[0]&&!$Q{noframes}[0]?qq| target="$_[0]"|:'').' style="margin:0;padding:0;">'.hidden('nocache',substr($^T,-6)).($Q{noframes}[0]?hidden('noframes','1'):'')}
sub frmpst{form('',$_[2]).hidden('action',$_[0]).hidden('session',$U{session}).($_[1]?hidden('what',$_[1]).hidden('sendto',$Q{sendto}[0]).hidden('multi',$Q{multi}[0]):'')}
sub frmlng{form('',$_[2]).hidden('action','language').hidden('nick',$Q{nick}[0]).hidden('hexpass',$Q{hexpass}[0]||he($Q{pass}[0])).($_[0]?hidden('do',$_[0]):'')}
sub frmset{form('',$_[2]).hidden('action','setup').hidden('nick',$Q{nick}[0]).hidden('hexpass',$Q{hexpass}[0]||he($Q{pass}[0])).($_[0]?hidden('do',$_[0]):'').($_[1]?hidden('what',$_[1]):'')}
sub frmadm{form('',$_[2]).hidden('action','admin').hidden('do',$_[0]).hidden('session',$U{session})}
# name/id  size  value maxlength  class  style
sub intext{qq|<input type="text" name="$_[0]" id="$_[0]" size="$_[1]"|.($_[2]ne''?qq| value="$_[2]"|:'').($_[3]?qq| maxlength="$_[3]"|:'').qq| class="$_[0]|.($_[4]?qq| $_[4]"|:'"').($_[3]&&$_[3]<9?qq| style="text-align:right;$_[5]"|:($_[5]?qq| style="$_[5]"|:'')).'>'}
#  name/id   size  class  style
sub inpass{qq|<input type="password" name="$_[0]" id="$_[0]" size="$_[1]"|.qq| class="$_[0]|.($_[2]?qq| $_[2]"|:'"').($_[3]?qq| style="$_[3]"|:'').'>'}
#   name/id   cols   rows   value   wrap   class  style
sub inarea{qq|<textarea name="$_[0]" id="$_[0]" cols="$_[1]" rows="$_[2]"|.($_[4]?qq| wrap="$_[4]"|:'').qq| class="$_[0]|.($_[5]?qq| $_[5]"|:'"').($_[6]?qq| style="$_[6]"|:'').($_[7]?' readonly':'').qq|>$_[3]</textarea>|}   
# name  value  checked? label  class style
sub inradio{qq|<input type="radio" name="$_[0]" id="$_[0]$_[1]" value="$_[1]" class="$_[0] $_[0]$_[1]|.($_[4]?" $_[4]":'').'"'.($_[5]?qq| style="$_[5]"|:'').($_[2]?' checked':'').qq|>&nbsp;<label for="$_[0]$_[1]" class="$_[0] $_[0]$_[1]|.($_[4]?" $_[4]":'').'"'.($_[5]?qq| style="$_[5]"|:'').">$_[3]</label>"}  
# name  value  checked? label  class style
sub incheck{qq|<input type="checkbox" name="$_[0]" id="$_[0]$_[1]" value="$_[1]" class="$_[0] $_[0]$_[1]|.($_[4]?" $_[4]":'').'"'.($_[5]?qq| style="$_[5]"|:'').($_[2]?' checked':'').qq|>&nbsp;<label for="$_[0]$_[1]" class="$_[0] $_[0]$_[1]|.($_[4]?" $_[4]":'').'"'.($_[5]?qq| style="$_[5]"|:'').">$_[3]</label>"}
# nick hex style selected?
sub nickopt{'<option '.($_[3]?'selected ':'').qq|value="$_[1]" class="chatter nick_$_[1]" style="$_[2]">$_[0]</option>|}
sub hidden{qq|<input type="hidden" name="$_[0]" value="$_[1]">|}
sub submit{qq|<input type="submit" class="$_[0]" value="|.htmlsafe($C{$_[0]}||$I{$_[0]}).($_[1]?qq|" style="$C{$_[1]}"|:'"').($_[2]?' disabled>':'>')}
sub thr{'<tr class="separator"><td'.($_[0]?qq| colspan="$_[0]"|:'').'><hr></td></tr>'}
sub thh{qq|<tr class="section $_[0]"><td colspan="2" align="center"><h3>$I{$_[0]}</h3></td></tr>|}
sub cfgta{qq|<tr class="$_[0]"><td align="left" valign="top">$I{$_[0]}</td><td align="right">|.inarea($_[0],'40','4',$C{$_[0]},'off').'</td></tr>'}
sub cfgt{qq|<tr class="$_[0]"><td align="left">$I{$_[0]}</td><td align="right">|.intext($_[0],$_[1],$C{$_[0]},$_[2],$_[0]).'</td></tr>'}
sub cfgts{cfgt($_[0],'7','6')}
sub cfgtm{cfgt($_[0],'30')}
sub cfgtb{cfgt($_[0],'50')}
sub bakarea{inarea('backupdata','80','8',$_[0],'off','backupdata','',$_[1])}
sub cfgyn{qq|<tr class="$_[0]"><td align="left">$I{$_[0]}</td><td align="right">|.inradio($_[0],'1',$C{$_[0]},$I{yes},'yes').'&nbsp;&nbsp;'.inradio($_[0],'0',!$C{$_[0]},$I{no},'no').'</td></tr>'}
sub gstset{qq|<td>&nbsp;</td><td align="left" class="guestset guestset$_[0]">|.inradio('guestset',$_[0],$_[0]==$T{guests},$_[1]).'</td><td>&nbsp;</td>'}
sub chtset{'<td>'.inradio('chatset',$_[0],$_[0]==$T{access},$_[1]).'</td><td>&nbsp;&nbsp;</td>'}
sub anchor{qq|<a name="$_[0]" style="background:transparent"><font size="1"><small>&nbsp;</small></font></a>|}
sub url{my$u="$S?nocache=".substr($^T,-6);$u.="&amp;noframes=1"if$Q{noframes}[0];while(my$n=shift){my$v=shift;$u.="&amp;$n=".urlsafe($v)}return$u}

sub print_start{my($css,$ref,$url)=@_;
	$url=~s/&amp;/&/g if$url;# Don't escape "&" in URLs here, it breaks some (older) browsers!
	print_headers();
	print "Refresh: $ref; URL=$url\n"if$url;
	print $H{begin_html},'<head>',$H{meta_html};
	print qq|<meta http-equiv="Refresh" content="$ref; URL=$url">\n|if$url;
	print_stylesheet($css);
	$H{begin_body}=~s/class="chat"/qq|class="$css|.($Q{noframes}[0]?' noframes':'').'"'/e;
	print '</head>',$H{begin_body};
	print_noframes(1);
}

sub linkrel{
	return unless $_[0];
	my($itype)=($_[0]=~/(?:data:image\/|\.)(x-icon|ico|gif|png)(?:;|$)/);
	$itype='x-icon'if'ico'eq$itype;
	$itype=qq| type="image/$itype"|if$itype;
	return qq|<link rel="shortcut icon" href="$_[0]"$itype>\n|;
}

sub send_redirect{my $href=$_[0];
	# Link redirection to strip off referers and prevent session leakage.
	send_error($I{errnolinks})if(($T{access}==ENA or $T{access}==STA) and (!$C{createlinks} or $C{useextderef}));
	# check for protocol, assume http if none given and correct the link accordingly.
	my ($scheme)=$href=~m~^([\w]*://|mailto:)~;
	if($scheme eq ''){$scheme='http://';$href=$scheme.$href}
	# Only do automatic refresh on http(s), else just give links
	if($scheme=~m~https?://~){
		if($C{showdisclaimer}){print_start('note')}else{print_start('note',0,$href)}
		print '<center>',$C{showdisclaimer}?format_text($C{disclaimer}):'',qq|<h2>$I{linkredirect}</h2><a href="$href">$_[0]</a></center>|;
	}else{
		$href=~s~^([\w]*://)?~http://~;
		print_start('note');
		print '<center>',$C{showdisclaimer}?format_text($C{disclaimer}):'',qq|<h2>$I{linknonhttp}</h2><a href="$_[0]">$_[0]</a><h2>$I{linktryhttp}</h2><a href="$href">$href</a></center>|;
	}
	print_end();
}

sub send_alogin{
	print_start('setup');
	print qq|<center>|,form(),hidden('action','setup'),qq|<table><tr><td align="left">$I{aloginname}</td><td>|,intext('nick','15'),qq|</td></tr><tr><td align="left">$I{aloginpass}</td><td>|,inpass('pass','15'),qq|</td></tr><tr><td colspan="2" align="right">|,submit('aloginbut'),qq|</td></tr></table></form></center>|;
	print_end();
}

sub send_language{
	print_start('setup');
	print qq|<center><h1>$I{lngheader}</h1><br><table cellspacing="0"><tr><td align="left"><table cellspacing="0"><tr><td>|,frmlng('backup'),submit('lngbackup'),qq|</form></td><td>&nbsp;&dArr;</td></tr></table></td></tr><tr><td>|,frmlng('restore','','method="post"'),qq|<table cellspacing="0"><tr><td>|,bakarea("$I{backdat}\n"),qq|</td></tr><tr><td align="right"><table cellspacing="0"><tr><td>&nbsp;&rArr;</td><td>|,submit('lngload'),qq|</td></tr></table></td></tr></table></form></td></table><br>|,frmlng('save','','method="post"'),qq|<table cellspacing="0" cellpadding="5" width="1"><tr><td colspan="2" align="left">$I{lnghelp}</td></tr><tr><td align="left"><h2>$I{lngtoken}</h2></td><td align="left"><h2>$I{lngdeftxt}</h2></td></tr><tr><td colspan=2 align="left"><hr></td></tr>|;
	my $start=tell(DATA);
	while(<DATA>){
		if($_=~/^#/){
			my ($sect)=$_=~/^#\s*(.+)/;
			print qq|<tr><td colspan="2" align="left"><hr></td></tr><tr><td colspan="2" align="left"><h3>$sect</h3></td></tr>|;
		}else{
			my($ikey,$ival)=$_=~/^([a-z_]+)\s*=(.+)/i;
			if($ikey and'stop_action'ne$ikey){
				my $rows=int(length($ival)/75)+1;
				$ival=formsafe($ival);
				$L{$ikey}=formsafe($L{$ikey});
				print qq|<tr><td valign="top" align="left">$ikey</td><td valign="top" align="left">$ival<br>|,inarea("edit_$ikey",'75',$rows,$L{$ikey},'virtual'),'</td></tr>';
			}
		}
	}
	seek(DATA,$start,0);
	print qq|<tr><td colspan="2" align="left"><hr></td></tr><tr><td colspan="2" align="center">|,submit('savechanges'),qq|</td></tr></table></form><br>$H{backtosetup}<br>$H{versiontag}</center>|;
	print_end();
}

sub send_setup{
	if($U{status}==SUP){
		read_members();
		$I{nickhelp}=~s/<MAX>/$C{maxname}/;
		$I{passhelp}=~s/<MIN>/$C{minpass}/;
		$I{membersdir}=~s/<DEFAULT>/$datadir/g;
	}
	print_start('setup');
	foreach(keys %C){next if $_ eq 'textfilters';$C{$_}=formsafe($C{$_})}
	print qq|<center><h2>$I{chatsetup}</h2>|,frmset('chataccess'),qq|<table cellspacing="0"><tr><td><b>$I{chataccess}</b></td><td>&nbsp;</td>|,chtset(SUS,$I{suspend}),chtset(ENA,$I{enabled}),chtset(STA,$I{staffonly}),chtset(LNK,$I{derefonly}),'<td>',submit('butset'),qq|</td></table></form><br><h2>$I{backups}</h2><table cellspacing="0"><tr><td align="left"><table cellspacing="0"><tr><td>|,frmset('backup','members'),submit('backmem'),qq|</form></td><td>&dArr;&nbsp;</td><td>|,frmset('backup','config'),submit('backcfg'),qq|</form></td><td>&dArr;&nbsp;</td></tr></table></td></tr><tr><td>|,frmset('restore','','method="post"'),qq|<table cellspacing="0"><tr><td>|,bakarea("$I{backdat}\n"),'</td></tr><tr><td align="right"><table cellspacing="0"><tr><td>&nbsp;&rArr;</td><td>',submit('restore'),'</td></tr></table></td></tr></table></form></td></tr></table><br>';
	if($U{status}==SUP){
		print qq|<h2>$I{directories}</h2>|,frmset('directories'),qq|<table cellspacing="5" width="80%"><tr><td align="justify" colspan="2">$I{dirsinfo}<br></td></tr>|,thr(2),cfgtm('membersdir'),thr(2),cfgtm('captchalibdir'),cfgtm('captchaimgdir'),thr(2),'<tr><td colspan="2" align="center">',submit('savedirs'),'</td></tr></table></form><br>';
		print qq|<h2>$I{mainadmins}</h2><i>$_[0]</i><table cellspacing="0">|,thr(),qq|<tr><td align="left"><b>$I{regadmin}</b></td></tr><tr><td align="right">|,frmset('mainadmin','new'),qq|<table cellspacing="0"><tr title="$I{nickhelp}"><td>&nbsp;</td><td align="left">$I{nickname}</td><td>|,intext('admnick','20'),qq|</td><td>&nbsp;</td></tr><tr title="$I{passhelp}"><td>&nbsp;</td><td align="left">$I{password}</td><td>|,intext('admpass','20'),qq|</td><td>|,submit('butregadmin'),qq|</td></tr></table></form></td></tr>|,thr(),qq|<tr><td align="left"><b>$I{raiseadmin}</b></td></tr><tr><td align="right">|,frmset('mainadmin','up'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td><select name="admnick" size="1" style="background-color:#$C{colbg}"><option value="">$I{selchoose}</option>|;
		print_memberslist(ADM);
		print qq|</select></td><td align="right">|,submit('butraise'),qq|</td></tr></table></form></td></tr>|,thr(),qq|<tr><td align="left"><b>$I{loweradmin}</b></td></tr><tr><td align="right">|,frmset('mainadmin','down'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td><select name="admnick" size="1" style="background-color:#$C{colbg}"><option value="">$I{selchoose}</option>|;
		print_memberslist(MAD);
		print qq|</select></td><td>|,submit('butlower'),qq|</td></tr></table></form></td></tr>|,thr(),qq|</table><br><br><h2>$I{cfglanguage}</h2>|,frmlng(),submit('editlanguage'),qq|</form><br>|,frmset('resetlanguage'),submit('resetlanguage','',!-e filepath('language')),qq|</form><br><h2>$I{cfgsettings}</h2>$I{cfgmainadm}<br><br>|;
	}else{
		print "<h2>$I{cfgsettings}</h2>",frmset('config','','method="post"'),'<table cellspacing="0">',thh('secgeneral'),thr(2),cfgtm('title'),cfgtm('favicon'),thr(2),cfgyn('redirifsusp'),cfgtm('redirtourl'),thr(2),cfgyn('allowfonts'),cfgyn('allowmultiline'),cfgyn('allowpms'),cfgyn('rndguestcol'),cfgyn('autocleanup'),cfgyn('keepguests'),thr(2),cfgyn('createlinks'),cfgts('maxlinklength'),cfgyn('showdisclaimer'),cfgyn('useextderef'),cfgtm('extderefurl'),thr(2),cfgyn('createatnicks'),cfgtm('atnicksym'),thr(2),cfgyn('splashshow'),cfgyn('splashall'),cfgyn('captchause'),cfgyn('captchaall');
		print_modules();
		print thr(2),cfgts('sessionexpire'),cfgts('guestsexpire'),cfgts('messageexpire'),cfgts('kickpenalty'),cfgts('captchaexpire'),cfgts('waitingexpire'),cfgts('guestspreserve'),thr(2),cfgts('hideguests'),thr(2),cfgts('defaultrefresh'),cfgts('minrefresh'),cfgts('maxrefresh'),cfgts('floodlimit'),thr(2),cfgts('boxwidthdef'),cfgts('boxheightdef'),cfgts('maxmessage'),cfgts('maxname'),cfgts('minpass'),thr(2),cfgt('gmtoffset','7','5'),thr(2),thh('secfilters'),thr(2);
		print_filters();
		print thr(2),'<tr id="placeholders"><td colspan="2" align="center">',format_info(),'</td></tr>',thr(2),thh('seccustom'),thr(2),cfgta('header'),cfgtm('noguests'),cfgtm('nomembers'),cfgtm('loginbutton'),cfgta('footer'),thr(2),cfgta('splashtxt'),cfgtm('splashcnt'),thr(2),cfgta('insideheader'),cfgta('insidefooter'),cfgt('frametopdef','5','4'),cfgt('framebottomdef','5','4'),thr(2),cfgta('disclaimer'),thr(2),thh('secrules'),thr(2),cfgta('rulestxt'),thr(2),cfgta('addhelpgst'),cfgta('addhelpreg'),cfgta('addhelpmod'),cfgta('addhelpadm'),thr(2),thh('secnotify'),thr(2),cfgtb('entrymessage'),cfgtb('logoutmessage'),cfgtb('kickederror'),thr(2),cfgtb('roomentry'),cfgtb('roomexit'),cfgtb('regmessage'),cfgtb('kickedmessage'),cfgtb('roomclean'),cfgtb('sysbefore'),cfgtb('sysafter'),thr(2),cfgtb('mesall'),cfgtb('mesmem'),cfgtb('messtaff'),cfgtb('mespm'),cfgtb('mesbefore'),cfgtb('mesafter'),cfgtm('sysnick'),thr(2),thh('secstyles'),thr(2),cfgts('colbg'),cfgts('coltxt'),cfgts('collnk'),cfgts('colvis'),cfgts('colact'),thr(2),cfgta('cssglobal'),cfgtb('styleback'),thr(2),cfgta('csslogin'),cfgtb('stylelogintext'),cfgtb('stylecolselect'),cfgtb('styleenter'),thr(2),cfgta('csssplash'),cfgtb('stylesplashcnt'),thr(2),cfgta('csswait'),cfgtb('stylewaitrel'),thr(2),cfgta('csspost'),cfgtb('styleposttext'),cfgtb('stylepostsend'),cfgtb('stylesendlist'),cfgtb('styledellast'),cfgtb('styledelall'),cfgtb('styleswitch'),thr(2),cfgta('cssview'),cfgtb('styletoplist'),cfgtb('styledelsome'),cfgtb('stylecheckwait'),thr(2),cfgta('csscontrols'),cfgtb('stylerelpost'),cfgtb('stylerelmes'),cfgtb('stylepause'),cfgtb('styleprofile'),cfgtb('styleadmin'),cfgtb('stylerules'),cfgtb('styleexit'),thr(2),cfgta('cssprofile'),thr(2),cfgta('cssrules'),thr(2),cfgta('cssnote'),thr(2),cfgta('cssadmin'),thr(2),cfgta('csssetup'),thr(2),cfgta('csserror'),thr(2),qq|<tr><td colspan="2" align="center"><small>$I{lastchanged} $C{lastchangedat}/$C{lastchangedby}</small><br><br></td></tr><tr><td colspan="2" align="center">|,submit('savechanges'),'</td></tr></table></form><br>';
	}
	print form(),hidden('action','setup'),submit('butlogout'),"</form><br>$H{versiontag}</center>";
	print_end();
}

sub print_modules{
	print qq|<tr id="captchamodule"><td align="left">$I{captchamodule}</td><td align="right"><select name="captchamodule" class="captchamodule|,$C{captchamodule}?" captcha$C{captchamodule}":'',qq|"><option value="" class="captchamodule">$I{selchoose}</option>|;
	foreach(get_captcha_modules()){print qq|<option value="$_" class="captchamodule captcha$_"|,$C{captchamodule}eq$_?' selected':'',qq|>$_</option>|}
	print '</select></td></tr>';
}

sub send_admin{
	read_members();
	print_start('admin');
	my $message=$_[0]?"<i>$_[0]</i>":'';$message=~s/<RECP>/hd($Q{name}[0])/eg;
	$I{admkick}=~s/<KICK>/$C{kickpenalty}/g;
	$I{nickhelp}=~s/<MAX>/$C{maxname}/g;
	$I{passhelp}=~s/<MIN>/$C{minpass}/g;
	my $chlist=qq|<select name="name" size="1" style="background-color:#$C{colbg}"><option value="">$I{selchoose}</option>|;foreach(sort {lc($a) cmp lc($b)} keys %P){$chlist.=nickopt($_,$P{$_}[0],$P{$_}[2])if($P{$_}[1]>=GST and $P{$_}[1]<$U{status})};$chlist.='</select>';
	print qq|<center><h2>$I{admheader}</h2>$message<table cellspacing="0">|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admclean}</b></td><td align="right">|,frmadm('clean','','method="get"'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td>|,inradio('what','room',0,$I{admcleanall}),'</td><td>&nbsp;</td><td>',inradio('what','choose',1,$I{admcleansome}),'</td><td>&nbsp;</td><td>',submit('butadmclean'),qq|</td></tr></table></form></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admkick}</b></td></tr><tr><td align="right">|,frmadm('kick'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td align="left" colspan="3">$I{admkickmes} |,intext('kickmessage','45'),qq|</td><td>&nbsp;</td></tr><tr><td>&nbsp;</td><td align="left">|,incheck('what','purge',0,$I{admkickpurge}),qq|</td><td>&nbsp;</td><td align="right">$chlist</td><td>|,submit('butadmkick'),qq|</td></tr></table></form></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{adminactive}</b></td><td align="right">|,frmadm('logout'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td valign="bottom">$chlist</td><td valign="bottom">|,submit('butadminactive'),qq|</td></tr></table></form></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admvsessions}</b></td><td align="right">|,frmadm('sessions'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td>|,submit('butadmview'),qq|</td></tr></table></form></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr class="admguests"><td align="left"><b>$I{admguests}</b></td></tr><tr class="admguests"><td align="right">|,frmadm('guests'),qq|<table cellspacing="0"><tr>|,gstset(FBD,$I{admguestsfbd}),qq|<td>&nbsp;</td></tr><tr>|,gstset(ALL,$I{admguestsall}),qq|<td>&nbsp;</td></tr><tr>|,gstset(STP,$I{admguestsstp}),qq|<td>&nbsp;</td></tr><tr>|,gstset(APP,$I{admguestsapp}),qq|<td valign="bottom">|,submit('butadmset'),'</td></tr></table></form></table></td></tr>',thr();
	if($U{status}>=ADM){
		print qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admregguest}</b></td><td align="right">|,frmadm('register'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td valign="bottom"><select name="name" size="1" style="background-color:#$C{colbg}"><option value="">$I{selchoose}</option>|;
		foreach(sort {lc($a) cmp lc($b)} keys %P){print nickopt($_,$P{$_}[0],$P{$_}[2])if $P{$_}[1]==GST}
		print '</select></td><td valign="bottom">',submit('butadmreg'),'</td></tr></table></form></td></tr></table></td></tr>',thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admmembers}</b></td></tr><tr><td align="right">|,frmadm('status'),qq|<table cellspacing="0"><tr><td>&nbsp;</td><td valign="bottom" align="right"><select name="name" size="1" style="background-color:#$C{colbg}"><option value="">$I{selchoose}</option>|;
		print_memberslist();
		print qq|</select><select name="set" size="1"><option value="">$I{selchoose}</option><option value="|.DEL.qq|">$I{selmemdelete}</option><option value="|.ACD.qq|">$I{selmemdeny} $I{symdenied}</option><option value="|.REG.qq|">$I{selmemreg}</option><option value="|.MOD.qq|">$I{selmemmod} $I{symmod}</option>|;
		print '<option value="'.ADM.qq|">$I{selmemadmin} $I{symadmin}</option>|if($U{status}==MAD);
		print '</select></td><td valign="bottom">',submit('butadmstatus'),'</td></tr></table></form></td></tr></table></td></tr>',thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{admregnew}</b></td></tr><tr><td align="right">|,frmadm('regnew'),qq|<table cellspacing="0"><tr title="$I{nickhelp}"><td>&nbsp;</td><td align="left">$I{nickname}</td><td>|,intext('name','20'),qq|</td><td>&nbsp;</td></tr><tr title="$I{passhelp}"><td>&nbsp;</td><td align="left">$I{password}</td><td>|,intext('pass','20'),'</td><td valign="bottom">',submit('butadmregnew'),'</td></tr></table></form></td></tr></table></td></tr>',thr();
	}
	print qq|</table><br>$H{backtochat}</center>|;
	print_end();
}

sub send_sessions{
	my @lines=parse_sessions(slurp_file('sessions',my$ferr));
	send_error($ferr)if$ferr;
	print_start('admin');
	print qq|<center><h2>$I{admsessions}</h2><table border="0" cellpadding="5">|;
	print qq|<thead valign="middle"><tr><th align="left"><b>$I{nicklist}</b></th><th align="center"><b>$I{timeoutin}</b></th><th align="center"><b>$I{ip}</b></th><th align="left"><b>$I{useragent}</b></th></tr></thead><tbody valign="middle">|;
	foreach(@lines){
		my %temp=sessionhash($_);
		print '<tr><td align="left">',style_nick($temp{nickname},$temp{fontinfo},$temp{status}),'</td><td align="center">'.get_timeout($temp{timestamp},$temp{status}),'</td><td align="center">',($U{status}>$temp{status}or$U{session}eq$temp{session})?qq|$temp{ip}</td><td align="left">$temp{useragent}|:'-</td><td align="left">-','</td></tr>';
	}
	print "</tbody></table><br>$H{backtochat}</center>";
	print_end();
}

sub send_suspended{
	print_start('error',0,$C{redirifsusp}?$C{redirtourl}:'');
	print "<h1>$I{suspended}</h1><p>",$C{redirifsusp}?qq|<a href="|.htmlsafe($C{redirtourl}).qq|">$I{redirtext}</a>|:$I{susptext},"</p><hr>";
	print_end();
}

sub get_chatterslist{
	my $lst=qq|<table cellspacing="0"><tr>|;
	get_waiting_count()if($T{guests}==APP and $U{status}>=MOD);
	if($T{waitings}){
		$I{butcheckwait}=~s/<COUNT>/$T{waitings}/g;
		$lst.=qq|<td valign="top">|.frmadm('newcomers').submit('butcheckwait','stylecheckwait').'</form></td><td>&nbsp;</td>';
	}
	$lst.=qq|<td valign="top"><b>$I{members}</b></td><td>&nbsp;</td><td valign="top">|.join(' &nbsp; ',@M).'</td>'.(@G?'<td>&nbsp;&nbsp;</td>':'')if@M;
	$lst.=qq|<td valign="top"><b>$I{guests}</b></td><td>&nbsp;</td><td valign="top">|.($T{guestcount}>=$C{hideguests}?0+@G:join(' &nbsp; ',@G)).'</td>'if@G;
	$lst.='</tr></table>';
	return $lst;
}

sub send_messages{
	my $url=url(action=>'view',session=>$U{session});
	if($Q{do}[0]eq'pause'){
		$I{butpauseinfo}=~s~<RELOAD>~<a href="$url">$I{butreloadm}</a>~g;
		$url=url(action=>'view',do=>'pause',session=>$U{session});
	}
	print_start('view',$U{refresh},$Q{do}[0]eq'pause'?'':$url);$url=$ENV{QUERY_STRING}?"$S?$ENV{QUERY_STRING}":$url;$url=~s/&(?!amp;)/&amp;/g;
	print_bar('top',$url,$Q{do}[0]eq'pause'?"<b>$I{butpauseinfo}</b>":get_chatterslist());
	print_messages();
	print_bar('bottom',$url);
	print_end();
}

sub send_choose_messages{
	my$url=$ENV{QUERY_STRING}?"$S?$ENV{QUERY_STRING}":url(action=>'admin',do=>'clean',session=>$U{session},what=>'choose');$url=~s/&(?!amp;)/&amp;/g;
	print_start('admin');
	print frmadm('clean'),hidden('what','selected');
	print_bar('top',$url,submit('butdelsome','styledelsome'));
	print_messages($U{status});
	print '</form>';
	print_bar('bottom',$url,$H{backtochat});
	print_end();
}

sub print_bar{# position,url,text
	my $nav=$_[0]eq'top'?'bottom':'top';
	my $nob='background:transparent';# remove background image and colour
	my $div='display:block;min-width:100%;max-width:100%;right:0;padding:0;margin:0;border-style:none';
	my $spc=qq|<div style="$div;$nob;height:3.5em;$_[0]:0;"><br></div>|if$_[2];# compensate space for pinned div
	$div.=';position:fixed;z-index:10000000000'if!$Q{noframes}[0];
	my $lne=qq|<div style="$div;$nob;height:1px;$_[0]:3em;background-color:#$C{coltxt};"></div>|if$_[2];# line
	$div.=$_[2]?";overflow:hidden;overflow-y:auto;height:3em;background-color:#$C{colbg};$C{styletoplist}":";$nob";
	print $spc,$lne if$_[0]eq'bottom';
	print anchor($_[0]),qq|<div id="$_[0]bar" class="bar" style="$div;$_[0]:0;"><table cellspacing="0" width="100%"><tr>|;
	print qq|<td align="left" valign="$_[0]">$_[2]</td><td>&nbsp;&nbsp;</td>|if$_[2];
	print qq|<td align="right" valign="$_[0]"><table cellspacing="0"><tr><td align="right"><span style="background-color:#$C{colbg};">&nbsp;<a href="$_[1]#$nav" id="nav$nav" class="nav">|,$I{"nav$nav"},qq|</a>&nbsp;</span></td></tr></table></td></tr></table></div>|;
	print $lne,$spc if$_[0]eq'top';
}

sub send_post{
	$U{postid}=substr($^T,-6);
	if($U{rejected}){
		$U{rejected}=htmlsafe($U{rejected});
		$U{rejected}=~s/<br>(<br>)+/<br><br>/g;
		$U{rejected}=~s/<br><br>$/<br>/;
		$C{allowmultiline}?$U{rejected}=~s/<br>/\n/g:$U{rejected}=~s/<br>/ /g;
		$U{rejected}=~s/^\s+|\s+$//g;
	}
	my $va=$Q{multi}[0]&&$C{allowmultiline}?'top':'bottom';
	print_start('post');
	print '<center>',format_text($C{insideheader}),'</center>'unless$Q{noframes}[0];
	print qq|<center><table cellspacing="0"><tr><td align="center">|,frmpst('post'),hidden('postid',$U{postid}),$C{allowmultiline}?hidden('multi',$Q{multi}[0]):'';
	print qq|<table cellspacing="0"><tr><td valign="$va" align="right" style="white-space:nowrap;">$U{displayname}&nbsp;:</td><td valign="$va">&nbsp;</td><td valign="$va">|;
	if($Q{multi}[0]&&$C{allowmultiline}){print inarea('message',$U{boxwidth},$U{boxheight},$U{rejected},'virtual','',($C{styleposttext}?"$C{styleposttext};":'')."background-color:#$C{colbg};border-color:#$U{colour};".get_style($U{fontinfo}))}
	else{print intext('message',$U{boxwidth},$U{rejected},$C{maxmessage},'',($C{styleposttext}?"$C{styleposttext};":'')."background-color:#$C{colbg};border-color:#$U{colour};".get_style($U{fontinfo}))}
	print qq|</td><td valign="$va">|,submit('butsendto','stylepostsend'),qq|</td><td valign="$va"><select name="sendto" size="1" style="|,$C{stylesendlist}?"$C{stylesendlist};":'',qq|background-color:#$C{colbg};color:#$C{coltxt}">|;
	print '<option ',$Q{sendto}[0]eq'*'?'selected ':'','value="*">-',$I{seltoall},'-</option>';
	print '<option ',$Q{sendto}[0]eq'?'?'selected ':'','value="?">-',$I{seltomem},'-</option>'if$U{status}>=REG;
	print '<option ',$Q{sendto}[0]eq'#'?'selected ':'','value="#">-',$I{seltoadm},'-</option>'if$U{status}>=MOD;
	if($C{allowpms}){foreach(sort {lc($a) cmp lc($b)} keys %P){print nickopt($_,$P{$_}[0],$P{$_}[2],$Q{sendto}[0]eq$P{$_}[0]?1:0)unless$U{nickname}eq$_}}
	print '</select></td></tr></table></form></td></tr><tr><td height="',($Q{multi}[0]&&$C{allowmultiline}?'4':'14'),'"></td></tr><tr><td align="center"><table cellspacing="0"><tr><td>',frmpst('delete','last'),submit('butdellast','styledellast'),'</form></td><td>',frmpst('delete','all'),submit('butdelall','styledelall'),'</form></td><td width="10"></td><td>';
	print frmpst('post'),hidden('sendto',$Q{sendto}[0]),hidden('multi',$Q{multi}[0]?'':'on'),submit($Q{multi}[0]?'butsingleline':'butmultiline','styleswitch'),'</form></td>'if$C{allowmultiline};
	print '</tr></table></td></tr></table></center>';
	print_end();
}

sub send_del_confirm{
	print_start('post');
	print '<center>',format_text($C{insideheader}),'</center>'unless$Q{noframes}[0];
	print qq|<center><table><tr><td>$I{delallconfirm}</td><tr><td height="8"></td></tr><tr><td align="center"><table cellspacing="0"><tr><td>|,frmpst('delete','allok'),submit('butdelall','styledelall'),'</form></td><td width="10"></td><td>',frmpst('post','cancel'),submit('butdelcancel'),'</form></td></tr></table></td></tr></table></center>';
	print_end();
}

sub send_help{
	print_start('rules');
	print "<h2>$I{rules}</h2>",rulestext(),"<br><br><hr><h2>$I{help}</h2>",helptext(),addhelptext(),"<hr><center>$H{backtochat}</center>";
	print_end();
}

sub send_profile{
	$I{passhelp}=~s/<MIN>/$C{minpass}/;
	$I{refreshrate}=~s/<MIN>/$C{minrefresh}/;
	$I{refreshrate}=~s/<MAX>/$C{maxrefresh}/;
	$I{entryrefresh}=~s/<DEFAULT>/$C{defaultrefresh}/;
	print_start('profile');
	print '<center>',form(),hidden('action','profile'),hidden('do','save'),hidden('session',$U{session}),qq|<h2>$I{profileheader}</h2><i>$_[0]</i><table cellspacing="0">|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr id="refreshrate"><td align="left"><b>$I{refreshrate}</b></td><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td>|,intext('refresh','3',$U{refresh},'3'),qq|</td></tr></table></td></tr></table></td></tr>|,thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr id="fontcolour"><td align="left"><b>$I{fontcolour}</b> (<a href="|,url(action=>'colours',session=>$U{session}),qq|" target="view">$I{viewcolours}</a>)</td><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td>|,intext('colour','7',$U{colour},'6'),qq|</td></tr></table></td></tr></table></td></tr>|,thr();
	if($U{status}>=REG and $C{allowfonts}){
		my $fopt='';my $usty='';my$fsel='';
		foreach(sort keys %F){
			my $fsty=get_style($F{$_}); 
			if($U{fontinfo}=~/$F{$_}/){$usty=qq| style="$fsty"|;$fsel=' selected'}else{$fsel=''}
			$fopt.=qq|<option$fsel value="$_" style="$fsty">$_</option>|;
		}
		print qq|<tr><td><table cellspacing="0" width="100%"><tr id="fontface"><td align="left"><b>$I{fontface}</b></td><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td><select name="font" id="font" size="1"$usty><option value="">* $I{fontdefault} *</option>|,$fopt,'</select></td><td>&nbsp;</td><td>',incheck('bold','on',($U{fontinfo}=~/<i?bi?>/)?1:0,"<b>$I{fontbold}</b>"),'</td><td>&nbsp;</td><td>',
		incheck('italic','on',($U{fontinfo}=~/<b?ib?>/)?1:0,"<i>$I{fontitalic}</i>"),'</td></tr></table></td></tr></table></td></tr>',thr();
	}elsif($U{status}>=REG){# keep switched off options in profile!
		foreach(keys %F){print hidden('font',$_)if$U{fontinfo}=~/$F{$_}/}
		print hidden('bold','on')if$U{fontinfo}=~/<i?bi?>/;
		print hidden('italic','on')if$U{fontinfo}=~/<b?ib?>/;
	}
	print qq|<tr id="fontexample"><td align="center">$U{displayname}&nbsp;: |,style_this($I{fontexample},$U{fontinfo}),'</td></tr>',thr(),qq|<tr><td><table cellspacing="0" width="100%"><tr id="boxsizes"><td align="left"><b>$I{boxsizes}</b></td><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td>$I{boxwidth}</td><td>|,intext('boxwidth','3',$U{boxwidth},'3'),$C{allowmultiline}?qq|</td><td>&nbsp;</td><td>$I{boxheight}</td><td>|.intext('boxheight','3',$U{boxheight},'3'):hidden('boxheight',$U{boxheight}),qq|</td></tr></table></td></tr></table></td></tr>|,thr();
	if($U{status}>=REG){
		print qq|<tr><td><table cellspacing="0" width="100%"><tr id="framesizes"><td align="left"><b>$I{framesizes}</b></td><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td>$I{frametop}</td><td>|,intext('frametop','3',$U{frametop},'4'),qq|</td><td>&nbsp;</td><td>$I{framebottom}</td><td>|,intext('framebottom','3',$U{framebottom},'4'),qq|</td></tr></table></td></tr></table></td></tr>|,thr(),qq|<tr id="entryrefresh"><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{entryrefresh}</b></td><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td>|,intext('entryrefresh','3',$U{entryrefresh},'3'),qq|</td></tr></table></td></tr></table></td></tr>|,thr(),qq|<tr id="exitoptions"><td><table cellspacing="0" width="100%"><tr><td align="left"><b>$I{exitoptions}</b></td><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td>|,incheck('exitdelpms','on',$U{exitdelpms},$I{exitdelpms}),'</td></tr></table></td></tr></table></td></tr>',thr();
	}
	print qq|<tr><td><table cellspacing="0" width="100%"><tr id="changepass"><td align="left"><b>$I{changepass}</b></td></tr><tr><td align="right"><table cellspacing="0"><tr><td>&nbsp;</td><td align="left">$I{oldpass}</td><td>|,inpass('oldpass','20'),qq|</td></tr><tr title="$I{passhelp}"><td>&nbsp;</td><td align="left">$I{newpass}</td><td>|,inpass('newpass','20'),qq|</td></tr><tr title="$I{passhelp}"><td>&nbsp;</td><td align="left">$I{confirmpass}</td><td>|,inpass('confirmpass','20'),'</td></tr></table></td></tr></table></td></tr>',thr(),'<tr><td align="center">',submit('savechanges'),"</td></tr></table></form><br>$H{backtochat}</center>";
	print_end();
}

sub send_controls{
	print_start('controls');
	print_controls();
	print '<center>',format_text($C{insidefooter}),'</center>';
	print_end();
}

sub print_controls{
	print '<center><table cellspacing="0"><tr><td>',form('post'),hidden('action','post'),hidden('session',$U{session}),submit('butreloadp','stylerelpost'),'</form></td><td>',form('view'),hidden('action','view'),hidden('session',$U{session}),submit('butreloadm','stylerelmes'),'</form></td><td>',form('view'),hidden('action','view'),hidden('do','pause'),hidden('session',$U{session}),submit('butpause','stylepause'),'</form></td><td>',form('view'),hidden('action','profile'),hidden('session',$U{session}),submit('butprofile','styleprofile'),'</form></td><td>',($U{status}>=MOD?(form('view'),hidden('action','admin'),hidden('session',$U{session}),submit('butadmin','styleadmin'),'</form></td><td>'):''),form('view'),hidden('action','help'),hidden('session',$U{session}),submit('butrules','stylerules'),'</form></td><td>',form('_parent'),hidden('action','logout'),hidden('session',$U{session}),submit('butexit','styleexit'),'</form></td></tr></table></center>';
}

sub print_noframes{
	return if!$Q{noframes}[0]or$Q{action}[0]!~/^(chat|view|post|delete|profile|colours|help|admin)$/;
	if($_[0]==1){print '<center>',format_text($C{insideheader}),'</center>'}else{print '<hr>'}
	print_controls();
	if($_[0]==2){print '<center>',format_text($C{insidefooter}),'</center>'}else{print '<hr>'}
}

sub send_frameset{
	send_noframes()if($Q{noframes}[0]);# manual ?noframes=1
	print_headers();
	print "$H{begin_frames}<head>$H{meta_html}";
	$H{begin_body}=~s/class="chat"/class="note noframes"/;
	print_stylesheet('note');
	print qq|</head>\n<frameset rows="$U{frametop},*,$U{framebottom}" border="3" frameborder="3" framespacing="3"><frame name="post" src="|,url(action=>'post',session=>$U{session}),q|"><frame name="view" src="|,url(action=>'view',session=>$U{session}),q|"><frame name="controls" src="|,url(action=>'controls',session=>$U{session}),qq|"><noframes>$H{begin_body}|;
	$Q{noframes}[0]=1;
	print_noframes(1);
	print "<center><br>$I{frames}<br><br></center>";
	print_noframes(2);
	print "$H{end_body}</noframes></frameset>$H{end_html}";
	exit;
}

sub send_noframes{
	print_start('note');
	print "<center><br>$I{frames}<br><br></center>";
	print_end();
}

sub send_entry{
	$I{reloadhelp}=~s/<REFRESH>/$U{entryrefresh}/g;
	print_start('note',$U{entryrefresh},url(action=>'chat',session=>$U{session}));
	print '<center><h2>',format_text($C{entrymessage}),"</h2></center><hr><small>$I{reloadhelp}</small><hr><center>",form('','method="get"'),hidden('action','chat'),hidden('session',$U{session}),submit('butreloadw','stylewaitrel'),'</form></center>';
	print_end();
}

sub send_logout{
	print_start('note');
	print '<center><h2>',format_text($C{logoutmessage}),"</h2>$H{backtologin}</center>";
	print_end();
}

sub send_colours{
	print_start('profile');
	print "<center><h2>$I{colheader}</h2><tt>";
	for(my $red=0x00;$red<=0xFF;$red+=0x33){ 
		for(my $green=0x00;$green<=0xFF;$green+=0x33){ 
			for(my $blue=0x00;$blue<=0xFF;$blue+=0x33){
				my $hcol=sprintf('%02X',$red).sprintf('%02X',$green).sprintf('%02X',$blue);
				print qq|<font color="#$hcol"><b>$hcol</b></font> |;
			}print '<br>';
		}print '<br>';
	}
	print "</tt>$H{backtoprofile}</center>";
	print_end();
}

sub send_login{
	$I{nickhelp}=~s/<MAX>/$C{maxname}/g;
	$I{passhelp}=~s/<MIN>/$C{minpass}/g;
	print_start('login');
	print '<center>',format_text($C{header}),form('_parent'),hidden('action','login'),qq|<table id="login" border="2" width="1" rules="none"><tr title="$I{nickhelp}"><td align="left">$I{nickname}</td><td align="right">|,intext('nick','15','','','',$C{stylelogintext}),qq|</td></tr><tr title="$I{passhelp}"><td align="left">$I{password}</td><td align="right">|,inpass('pass','15','',$C{stylelogintext}),'</td></tr>';
	if($T{access}==STA){
		print '<tr><td colspan="2" align="center">',format_text($C{nomembers}),'</td></tr>';
	}elsif($T{noguests}){
		print '<tr><td colspan="2" align="center">',format_text($C{noguests}),'</td></tr>';
	}else{
		print qq|<tr><td colspan="2" align="center">$I{selcolguests}<br><select style="$C{stylecolselect};color:#$C{coltxt};background-color:#$C{colbg};" name="colour"><option value="">* |,$C{rndguestcol}?$I{selcolrandom}:$I{selcoldefault},' *</option>';
		print_colours();
		print '</select></td></tr>';
	}
	print '<tr><td colspan="2" align="center">',submit('loginbutton','styleenter'),'</td></tr></table></form>',format_text($C{footer}),'</center>';
	print_end();
}

sub send_error{my($err,$mes)=@_;
	format_text($err);
	$mes=format_text($mes).'<br><br>'if$mes;
	print_start('error');
	print "<h2>$I{error} $err</h2>$mes$H{backtologin}";
	print_end();
}

sub send_fatal{
	return if$Q{action}[0]=~/^setup|init$/;
	set_config_defaults();
	set_html_vars();
	print_start('error');
	print "<h2>$I{fatalerror}</h2>$_[0]";
	print_end();
}

sub print_memberslist{
	foreach(sort {lc($a) cmp lc($b)} keys%A){
		print nickopt(format_nick($_,$_[0]?0:$A{$_}[1]),$A{$_}[0],$A{$_}[2])if(!$_[0]||$A{$_}[1]==$_[0]);
	}
}

######################################################################
# content filters
######################################################################

sub print_filters{
	print qq|<tr id="filterslist"><td colspan="2" align="left">$I{filterslist}</td></tr>|;
	my $i=1;foreach(split('<>',$C{textfilters})){print_filter($i++,$_)}
	print qq|<tr id="filtersnew"><td colspan="2" align="left">$I{filtersnew}</td></tr>|;
	print_filter();
}

sub print_filter{my($no,$filter)=@_;
	$no||='new';
	my %f=filterhash($filter);
	my $fchoosetype='';
	my $fchooseaction='';
	my @typesel;
	my @actionsel;
	my @activesel;
	my $rxerror;
	if($no eq 'new'){
		%f=(type=>$Q{ftypenew}[0],match=>$Q{fmatchnew}[0],action=>$Q{factionnew}[0],replace=>$Q{freplacenew}[0],priority=>$Q{fprioritynew}[0],valid=>'-');
		foreach(@{$Q{fvalidnew}}){$f{valid}.="$_-"};
		$fchoosetype=' selected'if$Q{ftypenew}[0]!~/^[1-2]$/;
		$fchooseaction=' selected'if$Q{factionnew}[0]!~/^[1-5]$/;
	}else{
		$fchoosetype=' disabled';
		$fchooseaction=' disabled';
		# compile regex and check for errors
		if($f{type}==2){
			my $rx='m/$f{match}/';
			eval $rx;
			if($@){
				$rxerror=qq|<span class="regexerror">$I{fregexerror}</span> &nbsp;|;
				$f{active}=2;
			}
		}
	}
	$typesel[$f{type}]=' selected' if $f{type}=~/^[1-2]$/;
	$actionsel[$f{action}]=' selected' if $f{action}=~/^[1-5]$/;
	$activesel[$f{active}]=' selected' if $f{active};
	$f{match}=htmlsafe($f{match});
	$f{replace}=htmlsafe($f{replace});
	print qq|<tr><td colspan="2" align="right"><select name="ftype$no" class="ftype ftype$f{type}"><option value="$f{type}" class="ftype"$fchoosetype>$I{fchoosetype}</option><option value="$f{type}" class="ftype" disabled>$I{fseparator}</option><option value="1" class="ftype ftype1"$typesel[1]>$I{ftypetext}</option><option value="2" class="ftype ftype2"$typesel[2]>$I{ftyperegex}</option></select>|,intext("fmatch$no",'60',$f{match},'','fmatch'),qq|</td></tr><tr><td colspan="2" align="right"><select name="faction$no" class="faction faction$f{action}"><option value="$f{action}" class="faction"$fchooseaction>$I{fchooseaction}</option><option value="$f{action}" class="faction" disabled>$I{fseparator}</option><option value="1" class="faction faction1"$actionsel[1]>$I{factionreplace}</option><option value="2" class="faction faction2"$actionsel[2]>$I{factionkick}</option><option value="3" class="faction faction3"$actionsel[3]>$I{factionpurge}</option><option value="4" class="faction faction4"$actionsel[4]>$I{factionsendpm}</option><option value="5" class="faction faction5"$actionsel[5]>$I{factionsysmes}</option></select>|,intext("freplace$no",'60',$f{replace},'','freplace'),qq|</td></tr><tr><td colspan="2" align="right">$I{fvalid}|;
	foreach(qw(GST REG MOD ADM)){print '&nbsp;',incheck("fvalid$no","$_",($f{valid}=~/$_/)?1:0,$I{"fvalid$_"},'fvalid')}
	print qq|</td></tr><tr><td colspan="2" align="right">|;
	print qq|$rxerror<select name="factive$no" class="factive factive$f{active}"><option value="1" class="factive factive1"$activesel[1]>$I{factive}</option><option value="2" class="factive factive2"$activesel[2]>$I{fdisabled}</option><option value="3" class="factive factive3">$I{fdelete}</option></select>&nbsp;|if $f{active};
	print qq|$I{fpriority}&nbsp;|,intext("fpriority$no",'2',$f{priority},'3','fpriority'),'</td></tr><tr><td colspan="2">&nbsp;</td></tr>';
}

sub filters_from_queries{
# type     0: undef   1: text      2: regex
# action   0: undef   1: replace   2: kick       3: purge    4: PM   5: notification
# active   0: undef   1: active    2: disabled   3: delete
# valid    -GST-REG-MOD-ADM-
# 'type"match"action"replacement"active"priority"valid<>....<>....<>'
	my @filter;my %f;
	for(my $i=1;;$i++){
		last if !$Q{"ftype$i"}[0];        # empty
		next if $Q{"factive$i"}[0]==3;    # delete
		next if $Q{"ftype$i"}[0]!~/^1|2$/;# invalid..
		next if $Q{"faction$i"}[0]!~/^[1-5]$/;
		next if $Q{"factive$i"}[0]!~/^1|2$/;
		%f=(type=>$Q{"ftype$i"}[0],match=>$Q{"fmatch$i"}[0],action=>$Q{"faction$i"}[0],replace=>$Q{"freplace$i"}[0],active=>$Q{"factive$i"}[0],priority=>$Q{"fpriority$i"}[0],valid=>'-');
		foreach(@{$Q{"fvalid$i"}}){$f{valid}.="$_-"};
		foreach(qw(match replace)){$f{$_}=~s/^\s+|\s+$//g}
		$f{active}=2 unless $f{match};
		$f{priority}=~s/\D|^0+$//g;
		push @filter,filterline(%f);
	}
	%f=(type=>$Q{ftypenew}[0],match=>$Q{fmatchnew}[0],action=>$Q{factionnew}[0],replace=>$Q{freplacenew}[0],active=>'1',priority=>$Q{fprioritynew}[0],valid=>'-');
	foreach(@{$Q{fvalidnew}}){$f{valid}.="$_-"};
	foreach(qw(match replace)){$f{$_}=~s/^\s+|\s+$//g}
	$f{priority}=~s/\D|^0+$//g;
	if($f{type}=~/^1|2$/&&$f{action}=~/^[1-5]$/&&$f{match}ne''){
		push @filter,filterline(%f);
		foreach(qw(ftypenew fmatchnew factionnew freplacenew fprioritynew fvalidnew)){$Q{$_}=[]}
	}
	@filter=sort filtersort @filter;
	return join('<>',@filter);
}

sub filterline{my%h=@_;join('"',$h{type},htmlsafe($h{match}),$h{action},htmlsafe($h{replace}),$h{active},$h{priority},$h{valid})}

sub filterhash{
	my %h;
	($h{type},$h{match},$h{action},$h{replace},$h{active},$h{priority},$h{valid})=split('"',$_[0]);
	$h{match}=htmlactive($h{match});
	$h{replace}=htmlactive($h{replace});
	return %h;
}

sub filtersort{
	my %ha=filterhash($a);my %hb=filterhash($b);
	if($ha{priority}==$hb{priority}){$ha{match} cmp $hb{match}}
	elsif($ha{priority}eq''){return 1}
	elsif($hb{priority}eq''){return -1}
	else{$ha{priority}<=>$hb{priority}}
}

sub apply_filters{
	foreach(split('<>',$C{textfilters})){
		my %f=filterhash($_);my $n;
		next unless $f{active}==1;# ignore inactive
		next if $f{match}eq'';# ignore empty filters
		next if $U{status}==GST&&$f{valid}!~/GST/;
		next if $U{status}==REG&&$f{valid}!~/REG/;
		next if $U{status}==MOD&&$f{valid}!~/MOD/;
		next if $U{status}>=ADM&&$f{valid}!~/ADM/;
		next if $f{action}==5&&$Q{sendto}[0]ne'*';# ignore if not public
		if($f{type}==1){# text
			$f{match}=~s/\s*\|\s*/|/g;
			$f{match}=~s/\|+/|/g;
			$f{match}=~s/^\||\|$//g;
			$f{match}=rxsafe($f{match},'\\|');
			my $rx='$n=($U{message}=~s/$f{match}/$f{replace}/ig)';
			eval $rx;
		}
		elsif($f{type}==2){# regex
			# Evaluating arbitrary user-input is a huge security risk!!!
			# => Escape all special characters, only allow $1,$2,.. for replacements.
			my $replace=rxsafe($f{replace},'\\$','|\\$(?![1-9])');
			my $rx='$n=($U{message}=~s/$f{match}/qq{qq{$replace}}/igsee)';
			eval $rx;
		}
		if($n>0){# matches found
			protect_tags($U{message});# if html was inserted protect from further filters!
			$U{filtered}=$f{action}if$f{action}>$U{filtered};# autokick or sys message
			if($f{action}==3){$U{kickmessage}=$f{replace}};
			if($f{action}==4){
				$U{sysmessage}=1;
				$Q{message}[0]='';
				$U{message}=$f{replace} if($f{type}==1||$f{replace}!~/[$][1-9]/);
				$U{poststatus}=SYS;
				$U{delstatus}=SYS;
				$U{recipient}=$U{nickname};
				$U{displayrecp}=$U{displayname};
				$U{displaysend}=$C{mespm};
			}
			if($f{action}==5){
				$U{sysmessage}=1;
				$Q{message}[0]='';
				$U{poststatus}=GST;
				$U{displaysend}='';
			}
		}
		last if $U{filtered}>=3;# stop filtering at kick+purge or PM/sys message
	}
}

sub rxsafe{my$rx=$_[0];$rx=~s/([^\w\d\s$_[1]]$_[2])/'\\x'.he($1)/ge;return$rx}

######################################################################
# login attempt
######################################################################

sub begin_login{
	$I{errbadnick}=~s/<MAX>/$C{maxname}/;
	$I{errbadpass}=~s/<MIN>/$C{minpass}/;
	$U{nickname}=cleanup_nick($Q{nick}[0]);
	$U{passhash}=hash_this($U{nickname}.$Q{pass}[0]);
	$U{colour}=$Q{colour}[0];
	$U{status}=NEW;
	send_error($I{errbadnick})if!valid_nick($U{nickname});
	check_session_reentry();# always let currently chatting nicks back in again
	check_member();# checked before allowed_nick/pass, or changes in settings could lock members out
	check_guests();# ... or known guests
	add_user_defaults();
	if($U{status}<REG){
		send_error($I{errnoguests})if($T{guests}==FBD);
		create_waiting_session()if$C{splashshow};
		if($T{guests}==APP){
			$U{status}=WNW;
			create_waiting_session();
		}
	}
	create_waiting_session()if$C{splashshow}&&$C{splashall};
	create_chatroom_session();
}

######################################################################
# splash screen and CAPTCHA handling, waiting file holds session
######################################################################

sub send_splash_screen{
	my $chtml=captcha_generate();
	print_start('splash');
	print '<center>',format_text($C{splashtxt}),'<br>',form(),hidden('action','splash'),hidden('session',$U{session}),"$chtml",submit('splashcnt','stylesplashcnt'),"</form><br><br>$H{backtologin}</center>";
	print_end();
}

sub update_splash_session{
	my$solved=shift;# captcha is solved? convert NEW to WNW
	my@lines=parse_waitings(open_file_rw(my$WAITING,'waiting',my$ferr));send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=sessionhash($_);
		if($temp{session}eq$U{session}){
			$U{timestamp}=$^T;
			if($solved){
				$U{status}=WNW if($U{status}==NEW&&$T{guests}==APP);
			}
			print $WAITING sessionline(%U);# always keep entry in case of doublepost
		}else{
			print $WAITING $_;
		}
	}
	$ferr=close_file($WAITING,'waiting');send_error($ferr)if$ferr;
	check_permittostay();
	create_chatroom_session()if$U{status}>GST&&!$C{captchaall};# bypass for members
}

sub captcha_generate{
	return''if!$C{captchause};
	return''if$U{status}>GST&&!$C{captchaall};# bypass for members
	my$modfile="$C{captchalibdir}/LeCaptcha$C{captchamodule}.pm";
	my$modname='LeCaptcha'.$C{captchamodule};
	if(-e$modfile){
		my$html;
		eval('require $modfile');send_error($I{errmodule},htmlsafe($@))if$@;
		eval('$html=$modname->generate_challenge(\%Q,\%C,\%K,\%I)');send_error($I{errmodule},htmlsafe($@))if$@;
		%K=store_captcha(%K);
		$html=~s/<IMAGE>/$S?action=captcha&amp;captchaid=$K{captchaid}/g;
		$html=hidden('captchaid',$K{captchaid}).$html;
		return $html;
	}
	send_error($I{errnocaptcha});
}

sub captcha_verified{
	return 1 if!$C{captchause};
	my$modfile="$C{captchalibdir}/LeCaptcha$C{captchamodule}.pm";
	my$modname='LeCaptcha'.$C{captchamodule};
	if(-e$modfile){
		my$success;
		eval('require $modfile');send_error($I{errmodule},htmlsafe($@))if$@;
		my @lines=open_file_rw(my$CAPTCHAS,'captchas',my$ferr);return 0 if$ferr;
		foreach(@lines){
			my %temp=captchahash($_);
			if($temp{captchaid}eq$Q{captchaid}[0]and$temp{session}eq$Q{session}[0]){%K=%temp}
			else{print $CAPTCHAS $_ unless expiredc($temp{timestamp})};
		}
		if($K{timestamp}){
			eval('$success=$modname->verify_response(\%Q,\%C,\%K,\%I)');send_error($I{errmodule},htmlsafe($@))if$@;
			if($success){
				$K{timestamp}=$^T;
				print $CAPTCHAS captchaline(%K);
			}
		}
		close_file($CAPTCHAS,'captchas',$ferr);return 0 if$ferr;
		return $success;
	}
	send_error($I{errnocaptcha});
}

sub send_captcha_image{
	send_error_image()if!$C{captchause};
	my$modfile="$C{captchalibdir}/LeCaptcha$C{captchamodule}.pm";
	my$modname='LeCaptcha'.$C{captchamodule};
	if(-e$modfile){
		%K=read_captcha((captchaid=>$Q{captchaid}[0]));send_error_image($K{error})if$K{error};
		eval('require $modfile');send_error_image($@)if$@;
		eval('$modname->output_image(\%Q,\%C,\%K,\%I)');send_error_image($@)if$@;
		exit;
	}
	send_error_image($I{errnocaptcha});
}

sub send_error_image{
	if(@_){my$err="@_";$err=~s/[\r\n]+/ /g;print "X-LeChat-Error: $err\n"}
	print "Content-Type: image/gif\nContent-Length: 147\n\n";
	binmode(STDOUT);
	print hd('47494638376110001000b30000000000999999ff0000ffffff0000000000000000000000000000000000000000000000000000000000000000000000002c000000001000100000044850884147a858eac0c1cdd2a0016415001a158cdfb9a9a874b932464f6b88c15abac33989e7d789c9863652eff8e1098327dbc813448a84a4e1eb2ac89266a9a9d7bbe498cf9c6b04003b');
	exit;
}

sub get_captcha_modules{
	my @modules;
	opendir(my$DIR,$C{captchalibdir}) or $_[0]="$I{errfile} ($C{captchalibdir})" and return;
	while(my$f=readdir($DIR)){if($f=~/^LeCaptcha(\w+)\.pm$/){push@modules,$1}}
	return sort {lc($a) cmp lc($b)} @modules;
}

sub store_captcha{
	my %c=@_;
	my %cids;
	my @lines=open_file_rw(my$CAPTCHAS,'captchas',my$ferr);return(error=>$ferr)if$ferr;
	foreach(@lines){
		my %temp=captchahash($_);
		$cids{$temp{captchaid}}=1;
		print $CAPTCHAS $_ unless expiredc($temp{timestamp});
	}
	do{$c{captchaid}=substr(hash_this(time.rand().$c{solution}),12)}while($cids{$c{captchaid}});
	$c{timestamp}=$^T;
	$c{session}=$U{session};
	$c{randseed}=int(rand(2147483647));# store random seed for reproducible image reloads
	print $CAPTCHAS captchaline(%c);
	close_file($CAPTCHAS,'captchas',$ferr);return(error=>$ferr)if$ferr;
	return %c;
}

sub read_captcha{
	my %c=@_;
	my @lines=slurp_file('captchas',my$ferr);return(error=>$ferr)if$ferr;
	foreach(@lines){
		my %temp=captchahash($_);
		if($c{captchaid}eq$temp{captchaid} and !expiredc($temp{timestamp})){
			srand($temp{randseed});# create reproducible output on image reload!
			return %temp;
		}
	}
	return(error=>$I{errexpired});
}

######################################################################
# session management
######################################################################

sub create_chatroom_session{
	my $inuse=0;my $known=0;my $reentry=0;
	# lock and update guests file first
	my @glines=parse_guests(open_file_rw(my$GUESTS,'guests',my$ferr));send_error($ferr)if$ferr;
	if($U{status}<=GST){
		foreach(@glines){
			my %temp=guesthash($_);
			if($temp{nickname}eq$U{nickname}){
				if($temp{passhash}eq$U{passhash}){
					%U=%temp;
					add_user_defaults();
					$known=1;
					$_=guestline(%U);
				}else{$inuse=1}
			}elsif(similar_nick($temp{nickname},$U{nickname})){$inuse=1}
		}
		unless($known||$inuse){# new name
			push(@glines,guestline(%U));
		}
		$U{status}=GST;
	}
	print $GUESTS @glines;
	# start session in room:
	unless($inuse){
		# read and update current sessions
		my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',$ferr));send_error($ferr)if$ferr;
		my %sids;my $kicked=0;
		for(my $i=$#lines; $i>=0;$i--){
			my %temp=sessionhash($lines[$i]);
			$sids{$temp{session}}=1;# collect all existing ids
			if($temp{nickname}eq$U{nickname}){# nick already here?
				if($U{passhash}eq$temp{passhash}){
					%U=%temp;
					add_user_defaults();
					$U{status}==KCK?$kicked=1:$reentry=1;
					splice(@lines,$i,1)if$reentry;
				}else{$inuse=1}
			}elsif(similar_nick($temp{nickname},$U{nickname})){
				$inuse=1 if $U{status}==GST;
			}
		}
		# create new session:
		unless($inuse||$kicked){
			unless($U{status}==GST&&$T{noguests}&&!$reentry){#
				do{$U{session}=hash_this(time.rand().$U{nickname})}while($sids{$U{session}});# check for hash collision
				push(@lines,sessionline(%U));
			}
		}
		print $SESSIONS @lines;
		$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	}
	# unlock guests file again
	$ferr=close_file($GUESTS,'guests');send_error($ferr)if$ferr;
	send_error($I{errbadlogin})if$inuse;
	check_permittostay();
	# cleanup empty room
	if(!keys%P){if($C{autocleanup}){clean_room()}else{del_private_messages()}}
	if($U{session}&&!$reentry){
		add_system_notification($C{roomentry})unless($U{status}==GST&&$T{guestcount}>=$C{hideguests});
	}
	send_entry();
}

sub kick_chatter{my($name,$mes)=@_;
	$U{displayrecp}='';
	my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',my$ferr));send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=sessionhash($_);
		if($temp{nickname}eq$name and $temp{status}!=KCK){
			if($U{status}>$temp{status} or $U{nickname}eq$name){# verify if status is sufficient to kick
				$temp{status}=KCK;
				$temp{timestamp}=60*($C{kickpenalty}-$C{guestsexpire})+$^T;
				$temp{kickmessage}=$mes;
				$_=sessionline(%temp);
				$U{displayrecp}=style_nick($temp{nickname},$temp{fontinfo});
			}
		}
	}
	print $SESSIONS @lines;
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	add_system_notification($C{kickedmessage})if$U{displayrecp};
	return $U{displayrecp};
}

sub logout_chatter{my $name=$_[0];
	my $lonick='';
	my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',my$ferr));send_error($ferr)if$ferr;
	for(my$i=$#lines; $i>=0;$i--){
		my%temp=sessionhash($lines[$i]);
		if($temp{nickname}eq$name and $temp{status}!=KCK){
			if($U{status}>$temp{status} or $U{nickname}eq$name){# verify if status is sufficient to logout
				splice(@lines,$i,1);
				$lonick=style_nick($temp{nickname},$temp{fontinfo});
			}
		}
	}
	print $SESSIONS @lines;
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	return $lonick;
}

sub update_session{
	my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',my$ferr));send_error($ferr)if$ferr;
	if($U{postid}eq$Q{postid}[0]){# ignore double post=reload from browser or proxy
		$Q{message}[0]='';
	}
	elsif(abs($^T-$U{timestamp})<=$C{floodlimit}){# time between posts too short, reject! (abs in case system clock jumped back)
		$U{rejected}=$Q{message}[0];
		$Q{message}[0]='';
	}
	else{
		validate_input();
		if($Q{message}[0]){
			$U{postid}=substr($Q{postid}[0],0,6);
			$U{timestamp}=$^T;
		}
	}
	foreach(@lines){
		my %temp=sessionhash($_);
		print $SESSIONS $_ if$temp{session}ne$U{session}||$Q{message}[0]eq'';
	}
	print $SESSIONS sessionline(%U) if$U{session}&&$Q{message}[0];
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	update_guest()if$U{status}==GST&&$Q{message}[0];# save guests file with new expires
	check_permittostay();
}

sub update_guest{
	return unless $U{status}==GST;
	my $found=0;
	my @lines=parse_guests(open_file_rw(my$GUESTS,'guests',my$ferr));send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=guesthash($_);
		if($temp{nickname}eq$U{nickname}){
			$U{expires}=$temp{expires};
			$_=guestline(update_expire(%U));
			$found=1;
		}
	}
	push(@lines,guestline(%U))unless$found;
	print $GUESTS @lines;
	$ferr=close_file($GUESTS,'guests');send_error($ferr)if$ferr;
}

sub remove_guest{
	my $nick=$_[0];$nick||=$U{nickname};
	my @lines=parse_guests(open_file_rw(my$GUESTS,'guests',my$ferr));send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=guesthash($_);
		print $GUESTS $_ unless $temp{nickname}eq$nick;
	}
	$ferr=close_file($GUESTS,'guests');send_error($ferr)if$ferr;
}

sub check_session{
	parse_sessions(slurp_file('sessions',my$ferr));
	send_error($ferr)if$ferr;
	check_permittostay();
}

sub check_session_reentry{
	# check if name is used in chat room already
	my @lines=parse_sessions(slurp_file('sessions',my$ferr));
	send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=sessionhash($_);
		if($temp{nickname}eq$U{nickname}){
			if($temp{passhash}eq$U{passhash}){# reentry, approved already
				%U=%temp;
				add_user_defaults();
				check_permittostay();
				create_chatroom_session();
			}else{
				send_error($I{errbadlogin});# wrong pass
			}
		}elsif(similar_nick($temp{nickname},$U{nickname})){
			send_error($I{errbadlogin})if$U{status}==NEW;# name in use
		}
	}
}

sub check_permittostay{
	send_error($I{errexpired})if!$U{session};
	send_error($C{kickederror},$U{kickmessage})if$U{status}==KCK;
	send_error($I{erraccdenied},$U{kickmessage})if$U{status}==WND||$U{status}==ACD;
	send_error($I{errnoguests})if$U{status}<GST&&$T{noguests};
	send_error($I{errnoguests})if$U{status}==GST&&$T{noguests}&&!$C{keepguests};
	send_error($I{errnomembers})if$U{status}<MOD&&$T{access}==STA;
}

sub exit_session{
	my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',my$ferr));send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=sessionhash($_);
		print $SESSIONS $_ if!($temp{session}eq$U{session}&&$U{status}!=KCK);
	}
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	update_guest()if$U{status}==GST;
	check_permittostay();
	add_system_notification($C{roomexit})unless($U{status}==GST&&$T{guestcount}>=$C{hideguests});
	del_private_messages($U{nickname})if$U{exitdelpms};
	# clean empty room
	if(!keys%P){if($C{autocleanup}){clean_room()}else{del_private_messages()}}
}
sub rewrite_sessions{
	my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',my$ferr));send_error($ferr)if$ferr;
	print $SESSIONS @lines;
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
}

sub read_sessions{
	parse_sessions(slurp_file('sessions',my$ferr));
	send_error($ferr)if$ferr;
}

sub parse_sessions{my @lines=@_;
# returns cleaned up sessions and populates global variables
	my %temp;my $i;%P=();@G=();@M=();@S=();$T{staffcount}=0;$T{guestcount}=0;
	# we need staff and guest counts first
	for($i=$#lines; $i>=0;$i--){
		%temp=sessionhash($lines[$i]);
		if(!valid_session_status($temp{status}) or expireds($temp{timestamp},$temp{status}) or ($temp{status}!=KCK and ($T{access}==SUS or $T{access}==LNK or ($T{access}==STA and $temp{status}<MOD)))){
			splice(@lines,$i,1);
		}elsif($temp{status}>=MOD){
			$T{staffcount}++;
		}elsif($temp{status}==GST){
			$T{guestcount}++;
		}
	}
	# fill variables, clean up guests if needed
	$T{noguests}=(($T{guests}==FBD) or (($T{guests}==APP or $T{guests}==STP) and $T{staffcount}==0))?1:0;
	for($i=$#lines; $i>=0;$i--){
		%temp=sessionhash($lines[$i]);
		if($temp{session}eq$Q{session}[0]){
			%U=%temp;
			add_user_defaults();
			next if$Q{action}[0]eq'logout';
		}
		if($temp{status}>=REG){
			$P{$temp{nickname}}=[he($temp{nickname}),$temp{status},get_style($temp{fontinfo})];
			push(@M,style_nick($temp{nickname},$temp{fontinfo}));
			push(@S,style_nick($temp{nickname},$temp{fontinfo}))if$temp{status}>=MOD;
		}elsif($temp{status}==GST){
			if($T{noguests} and !$C{keepguests}){
				splice(@lines,$i,1);
			}else{
				$P{$temp{nickname}}=[he($temp{nickname}),$temp{status},get_style($temp{fontinfo})];
				push(@G,style_nick($temp{nickname},$temp{fontinfo}));
			}
		}
	}
	return @lines;
}

######################################################################
# waiting room handling
######################################################################

sub create_waiting_session{
	# remove expired waiting entries
	my@lines=parse_waitings(open_file_rw(my$WAITING,'waiting',my$ferr));send_error($ferr)if$ferr;
	my %sids;my $reentry;my $inuse;
	foreach(@lines){
		my %temp=sessionhash($_);
		$sids{$temp{session}}=1;# collect all existing ids
		if(similar_nick($temp{nickname},$U{nickname})){# nick already waiting?
			if($U{passhash}eq$temp{passhash}){
				$reentry=1;
				if($U{status}>=GST&&$temp{status}!=$U{status}){# recent status change!!
					$U{session}=$temp{session};# just get old waiting session-id
				}else{
					%U=%temp;
				}
				add_user_defaults();
				$_=sessionline(%U);
			}else{
				$inuse=1;
			}
		}
	}
	# create new waiting session:
	unless($inuse and $U{status}<REG or $reentry){
		add_user_defaults();
		do{$U{session}=substr(hash_this(time.rand().$U{nickname}),16)}while($sids{$U{session}});# check for hash collision
		push(@lines,sessionline(%U));
	}
	print $WAITING @lines;
	$ferr=close_file($WAITING,'waiting');send_error($ferr)if$ferr;
	send_error($I{errbadlogin})if$inuse;
	check_permittostay();
	send_waiting_room()if$U{status}==WNW;
	send_splash_screen();
}

sub check_waiting_session{
	parse_waitings(slurp_file('waiting',my$err));
	send_error($err)if$err;
	check_permittostay();
	if($U{status}==WNA){# approved
		$U{status}=GST;
		add_user_defaults();
		create_chatroom_session();
		send_entry();
	}
}

sub cleanup_waiting_sessions{
	# cleanup waitings if guestroom gets opened
	my @lines=parse_waitings(open_file_rw(my$WAITING,'waiting',my$ferr));return if$ferr;
	foreach(@lines){
		my %temp=sessionhash($_);
		if($temp{status}==WNW){
			$temp{status}=WNA;
			$_=sessionline(%temp);
		}
		print $WAITING $_;
	}
	$ferr=close_file($WAITING,'waiting');
}

sub wait_progress{
	my$left=int(($^T-$U{timestamp})/2)%100;my$right=100-$left;# pseudo progress bar
	return qq|<br><br><table border="1" bordercolor="#$C{coltxt}" width="50%"><tr><td bgcolor="#$C{coltxt}" width="$left%"><small>&nbsp;</small></td><td bgcolor="#$C{colbg}"width="$right%"><small>&nbsp;</small></td></tr></table>|;
}

sub send_waiting_room{
	format_text($I{waitmessage});
	$I{reloadhelp}=~s/<REFRESH>/$C{defaultrefresh}/;
	print_start('wait',$C{defaultrefresh},url(action=>'wait',session=>$U{session}));
	print qq|<center><h1>$I{waitroom}</h1>$I{waitmessage}<br>|,wait_progress(),qq|<br></center><hr><small>$I{reloadhelp}</small><hr><center>|,form(),hidden('action','wait'),hidden('session',$U{session}),submit('butreloadw','stylewaitrel'),'</form></center>';
	print_end();
}

sub send_waiting_admin{
	my @lines=parse_waitings(slurp_file('waiting',my$ferr));
	send_error($ferr)if$ferr;
	print_start('admin');
	print qq|<center><h2>$I{admwaiting}</h2>|;
	if($T{waitings}){
		print form(),hidden('action','admin'),hidden('do','newcomers'),hidden('session',$U{session}),qq|<table cellpadding="5"><thead align="left"><tr><th><b>$I{nicklist}</b></th><th><b>$I{ip}</b></th><th><b>$I{useragent}</b></th></tr></thead><tbody align="left" valign="middle">|;
		foreach(@lines){
			my %temp=sessionhash($_);
			next if$temp{status}!=WNW;
			print '<tr><td>',hidden('alls',$temp{hex}),incheck('cn',$temp{hex},0,style_nick($temp{nickname},$temp{fontinfo})),"</td><td>$temp{ip}</td><td>$temp{useragent}</td></tr>";
		}
		print '</tbody></table><br><table><tr class="allowdeny"><td>',inradio('what','allowchecked',1,$I{allowchecked},'allowdeny'),'</td><td>&nbsp;&nbsp;</td><td>',inradio('what','allowall',0,$I{allowall},'allowdeny'),'</td><td>&nbsp;&nbsp;</td><td>',inradio('what','denychecked',0,$I{denychecked},'allowdeny'),'</td><td>&nbsp;&nbsp;</td><td>',inradio('what','denyall',0,$I{denyall},'allowdeny'),qq|</td></tr><tr class="allowdeny"><td colspan="7" align="center">$I{denymessage}&nbsp;|,intext('kickmessage','45'),'</td></tr><tr class="allowdeny"><td colspan="7" align="center">',submit('butallowdeny'),'</td></tr></table></form><br>';
	}else{
		print "$I{waitempty}<br><br>";
	}
	print "$H{backtochat}</center>";
	print_end();
}

sub get_waiting_count{
	# return number of sessions to be approved, for admin-button
	parse_waitings(slurp_file('waiting',my$ferr));
	send_error($ferr)if$ferr;
	return $T{waitings};
}

sub parse_waitings{my @lines=@_;
	# returns cleaned up sessions and populates global variables
	$T{waitings}=0;
	for(my $i=$#lines; $i>=0;$i--){
		my %temp=sessionhash($lines[$i]);
		if(expiredw($temp{timestamp})){
			splice(@lines,$i,1);
		}else{
			if($Q{session}[0]eq$temp{session}){
				%U=%temp;
				add_user_defaults();
			}
			$T{waitings}++ if $temp{status}==WNW;
		}
	}
	return @lines;
}

sub edit_waiting_sessions{
	my$newstatus=$_[0]=~/^allow(checked|all)$/?WNA:$_[0]=~/^deny(checked|all)$/?WND:0;
	return unless$newstatus;
	my%cns=();foreach(@{$Q{$_[0]=~/all$/?'alls':'cn'}}){$cns{$_}=1}
	my @lines=parse_waitings(open_file_rw(my$WAITING,'waiting',my$ferr));send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=sessionhash($_);
		if($temp{status}==WNW and $cns{$temp{hex}}){
			$temp{status}=$newstatus;
			$temp{kickmessage}=$Q{kickmessage}[0]if$newstatus==WND;
		}
		$_=sessionline(%temp);
	}
	print $WAITING @lines;
	$ferr=close_file($WAITING,'waiting');send_error($ferr)if$ferr;
}

######################################################################
# member handling
######################################################################

sub valid_admin{
	($U{nickname},$U{pass},$U{hexpass})=@_;
	$U{pass}||=hd($U{hexpass});# masked pass on setup pages
	# superuser?
	$U{passhash}=hash_this($U{nickname}.hash_this($U{nickname}).hash_this($U{pass}).$U{pass});
	my($sudata)=slurp_file('admin',my$ferr);
	send_error($ferr)if$ferr;
	if($U{passhash}eq$sudata){
		$U{status}=SUP;
		return SUP;
	}
	# main admin?
	$U{passhash}=hash_this($U{nickname}.$U{pass});
	my @lines=slurp_file('members',$ferr);
	send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=memberhash($_);
		return MAD if($temp{nickname}eq$U{nickname}&&$temp{passhash}eq$U{passhash}&&$temp{status}==MAD);
	}
	# no admin
	return 0;
}

sub check_member{
	my @lines=slurp_file('members',my$ferr);
	send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=memberhash($_);
		if($temp{nickname}eq$U{nickname}){
			if($temp{passhash}eq$U{passhash}){
				%U=%temp;
				last;
			}else{send_error($I{errbadlogin})}
		}
		$T{similarnick}=1 if similar_nick($temp{nickname},$U{nickname});
	}
	send_error($I{erraccdenied})if($U{status}==ACD||$U{status}>MAD);
}

sub read_members{
	my @lines=slurp_file('members',my$ferr);
	send_error($ferr)if$ferr;
	%A=(); 
	foreach(@lines){
		my %temp=memberhash($_);
		$A{$temp{nickname}}=[$temp{hex},$temp{status},get_style("#$temp{colour} $F{$temp{fontface}} <$temp{fonttags}>")];
	}
}

sub parse_guests{my @lines=@_;
	for(my $i=$#lines; $i>=0;$i--){
		my %temp=guesthash($lines[$i]);
		splice(@lines,$i,1) if $^T>$temp{expires};
	}
	return @lines;
}

sub check_guests{
	return if $U{status}>GST;# already member
	my @lines=parse_guests(slurp_file('guests',my$ferr));send_error($ferr)if$ferr;
	my $known=0;
	foreach(@lines){
		my %temp=guesthash($_);
		if($temp{nickname}eq$U{nickname}){
			if($temp{passhash}eq$U{passhash}){
				%U=%temp;
				$known=1;
				last;
			}else{send_error($I{errbadlogin})}
		}
		$T{similarnick}=1 if similar_nick($temp{nickname},$U{nickname});
	}
	send_error($I{errbadlogin})if!$known&&$T{similarnick};
	send_error($I{errbadnick})if!$known&&!allowed_nick($U{nickname}); 
	send_error($I{errbadpass})if!$known&&!allowed_pass($Q{pass}[0]);
	del_private_messages($U{nickname})if!$known;# in case someone else used the name before
}

sub register_guest{
	send_admin()if$Q{name}[0]eq'';
	if($P{hd($Q{name}[0])}[1]!=GST){
		send_admin($I{errcantreg});
	}
	my @lines=open_file_rw(my$SESSIONS,'sessions',my$ferr);send_error($ferr)if$ferr;
	my %reg;
	foreach(@lines){
		my %temp=sessionhash($_); 
		if(he($temp{nickname})eq$Q{name}[0]&&$temp{status}==GST){
			$temp{status}=REG;
			%reg=%temp;
			($reg{colour})=$reg{fontinfo}=~/#([a-f0-9]{6})/i;
			print $SESSIONS sessionline(%temp);
		}
		else{
			print $SESSIONS $_ if!expireds($temp{timestamp},$temp{status});
		}
	}
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	if($reg{status}!=REG){
		send_admin($I{errcantreg});
	}
	@lines=open_file_rw(my$MEMBERS,'members',$ferr);send_error($ferr)if$ferr;
	print $MEMBERS @lines;
	foreach(@lines){
		my %temp=memberhash($_);
		if(he($temp{nickname})eq$Q{name}[0]){
			$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
			send_admin($I{erralreadyreg});
		}
	}
	print $MEMBERS memberline(%reg);
	$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
	$U{displayrecp}=style_nick($reg{nickname},$reg{fontinfo});
	remove_guest(hd($Q{name}[0]));
	add_system_notification($C{regmessage});
}

sub register_new{
	$Q{name}[0]=cleanup_nick($Q{name}[0]);
	send_admin()if$Q{name}[0]eq'';
	$I{errbadnick}=~s/<MAX>/$C{maxname}/;
	$I{errbadpass}=~s/<MIN>/$C{minpass}/;
	if($P{$Q{name}[0]}){
		$I{errcantregnew}=~s/<RECP>/$Q{name}[0]/;
		send_admin($I{errcantregnew});
	}
	send_admin($I{errbadnick})if!valid_nick($Q{name}[0]);
	send_admin($I{errbadpass})if!allowed_pass($Q{pass}[0]);
	remove_guest($Q{name}[0]);# just in case
	my @lines=open_file_rw(my$MEMBERS,'members',my$ferr);send_error($ferr)if$ferr;
	print $MEMBERS @lines;
	foreach(@lines){
		my %temp=memberhash($_);
		if($temp{nickname}eq$Q{name}[0]){
			$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
			$I{erralreadyreg}=~s/<RECP>/$Q{name}[0]/;
			send_admin($I{erralreadyreg});
		}
	}
	my %reg=(
		nickname=>$Q{name}[0],
		passhash=>hash_this($Q{name}[0].$Q{pass}[0]), 
		status  =>REG,
		colour  =>$C{coltxt},
	);
	print $MEMBERS memberline(%reg);
	$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
	$I{succreg}=~s/<RECP>/$Q{name}[0]/;
	send_admin($I{succreg});
}

sub change_status{
	send_admin()if($Q{name}[0]eq''||$Q{set}[0]eq'');
	if($U{status}<=$Q{set}[0]||!valid_member_status($Q{set}[0])){
		send_admin($I{errcantstatus})
	}
	my $found=0;
	my $nick=hd($Q{name}[0]);
	my @lines=open_file_rw(my$MEMBERS,'members',my$ferr);send_error($ferr)if$ferr;
	foreach(@lines){
		my %temp=memberhash($_);
		if($temp{nickname}eq$nick&&$U{status}>$temp{status}){
			$found=1;
			next if$Q{set}[0]==DEL;
			$found=2;
			$temp{status}=$Q{set}[0];
			print $MEMBERS memberline(%temp);
		}
		else{
			print $MEMBERS $_;
		}
	}
	$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
	if($found==1){
		send_admin($I{succdelmem})  
	}
	elsif($found==2){
		send_admin($I{succstatus})  
	}else{
		send_admin($I{errcantstatus})
	}
}

sub save_profile{
	if(!$Q{oldpass}[0]&&($Q{newpass}[0]||$Q{confirmpass}[0])){
		check_session();
		send_profile($I{errwrongpass});
	}
	if($Q{newpass}[0]ne$Q{confirmpass}[0]){
		check_session();
		send_profile($I{errdiffpass});
	}
	if($Q{oldpass}[0]&&!allowed_pass($Q{newpass}[0])){
		$I{errbadpass}=~s/<MIN>/$C{minpass}/;
		check_session();
		send_profile($I{errbadpass});
	}
	# check and rewrite session
	my @lines=parse_sessions(open_file_rw(my$SESSIONS,'sessions',my$ferr));send_error($ferr)if$ferr;
	$U{oldhash}=$Q{oldpass}[0]?hash_this($U{nickname}.$Q{oldpass}[0]):$U{passhash};
	$U{newhash}=$Q{newpass}[0]?hash_this($U{nickname}.$Q{newpass}[0]):$U{passhash};
	$U{orihash}=$U{passhash};
	foreach(@lines){
		my %temp=sessionhash($_);
		if($temp{session}eq$U{session}&&$temp{status}>=GST&&$temp{passhash}eq$U{oldhash}){
			amend_profile();
			$U{passhash}=$U{newhash};
			print $SESSIONS sessionline(%U);
		}else{
			print $SESSIONS $_;
		}
	}
	$ferr=close_file($SESSIONS,'sessions');send_error($ferr)if$ferr;
	check_permittostay();
	send_profile($I{errwrongpass})if$U{orihash}ne$U{oldhash};
	# rewrite member file
	if($U{status}>=REG){
		my $err='';
		my @lines=open_file_rw(my$MEMBERS,'members',$ferr);send_error($ferr)if$ferr;
		foreach(@lines){
			my %temp=memberhash($_);
			if($temp{nickname}eq$U{nickname}){
				$U{sessionstatus}=$U{status};
				$U{status}=$temp{status};
				$err=$I{errwrongpass}if$temp{passhash}ne$U{orihash};
				print $MEMBERS $err?$_:memberline(%U);
				$U{status}=$U{sessionstatus};
			}
			else{
				print $MEMBERS $_;
			}
		}
		$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
		send_profile($err)if$err;
	}elsif($U{status}==GST){# rewrite guests file
		update_guest();
	}
	send_profile($I{succchanged});
}

sub amend_profile{
	foreach(qw(refresh boxwidth boxheight entryrefresh)){$U{$_}=$Q{$_}[0]||'';$U{$_}=~y/0-9//cd;$U{$_}=~s/^0+//}
	foreach(qw(frametop framebottom)){$U{$_}=$Q{$_}[0]||'';$U{$_}=~y/0-9%//cd;$U{$_}=~s/^0+|%(?!$)//g}
	$U{colour}=($Q{colour}[0]=~/^[a-f0-9]{6}$|^$/i)?$Q{colour}[0]:$U{colour};
	$U{fonttags}='';
	$U{fonttags}.='b'if($Q{bold}[0]&&$U{status}>=REG);
	$U{fonttags}.='i'if($Q{italic}[0]&&$U{status}>=REG);
	$U{fontface}=$Q{font}[0]if($F{$Q{font}[0]}&&$U{status}>=REG);
	$U{fontinfo}='';
	$U{exitdelpms}=($Q{exitdelpms}[0]&&$U{status}>=REG)?'1':'';
	add_user_defaults();
}

sub rangecheck{
	my($val,$def,$min,$max)=@_;
	if($val=~/%$/){$min='1%';$max='98%'}
	return $def if''eq$val;
	return $min if$val<$min;
	return $max if$val>$max;
	return $val;
}

sub add_user_defaults{
	$U{ip}=htmlsafe($ENV{REMOTE_ADDR});
	$U{useragent}=htmlsafe($ENV{HTTP_USER_AGENT});
	$U{timestamp}||=$^T;
	$U{postid}||='OOOOOO';
	$U{refresh}=rangecheck($U{refresh},$C{defaultrefresh},$C{minrefresh},$C{maxrefresh});
	unless($U{fontinfo}){
		unless($U{colour}=~/^[a-f0-9]{6}$/i){
			if($C{rndguestcol}){do{$U{colour}=sprintf('%02X',int(rand(256))).sprintf('%02X',int(rand(256))).sprintf('%02X',int(rand(256)))}until(abs(greyval($U{colour})-greyval($C{colbg}))>75);
			}else{$U{colour}=$C{coltxt}}
		}
		$U{fontinfo}="#$U{colour} $F{$U{fontface}} <$U{fonttags}>";
	}
	($U{colour})=$U{fontinfo}=~/#([0-9A-Fa-f]{6})/;
	$U{displayname}=style_nick($U{nickname},$U{fontinfo});
	$U{boxwidth}=rangecheck($U{boxwidth},$C{boxwidthdef},10,999);
	$U{boxheight}=rangecheck($U{boxheight},$C{boxheightdef},2,999);
	$U{frametop}=rangecheck($U{frametop},$C{frametopdef},50,9999);
	$U{framebottom}=rangecheck($U{framebottom},$C{framebottomdef},50,9999);
	$U{entryrefresh}=rangecheck($U{entryrefresh},$C{defaultrefresh},1,$C{maxrefresh});
	$U{exitdelpms}=''unless($U{status}>=REG&&$U{exitdelpms}eq'1');
	%U=update_expire(%U)if($U{status}<=GST&&$U{status}>=NEW);
}

sub update_expire{my%u=@_;
	# calculate minimum needed preservation of guest logins against imposters and later PM-reading for current room, always keep maximum if bigger already from another connected room
	my $expires=$^T+(($C{guestsexpire}+$C{messageexpire})>($C{guestspreserve}*60)?(($C{guestsexpire}+$C{messageexpire})*60):($C{guestspreserve}*3600));
	$u{expires}=($expires>$u{expires})?$expires:$u{expires};
	return %u;
}

######################################################################
# message handling
######################################################################

sub validate_input{
	validate_post();
	return unless $Q{message}[0];# no valid post happening
	$U{message}=substr($Q{message}[0],0,$C{maxmessage});
	$U{rejected}||=substr($Q{message}[0],$C{maxmessage});
	if($U{message}=~/&[^;]{0,10}$/&&$U{rejected}=~/^([^;]{0,10};)/){
		$U{message}.=$1;
		$U{rejected}=~s/^$1//;
	}
	$U{message}=htmlsafe($U{message});
	$U{message}=~s/<br>/\n/g;
	apply_filters();
	return if $U{filtered}=~/3|4/;
	if($C{allowmultiline}&&$Q{multi}[0]){
		$U{message}=~s/\n/<br>/g;
		$U{message}=~s/<br>(<br>)+/<br><br>/g;
		$U{message}=~s/<br><br>$/<br>/;
		$U{message}=~s/  / &nbsp;/g;
		$U{message}=~s/<br> /<br>&nbsp;/g;
	}else{
		$U{message}=~s/\n/ /g;
		$U{message}=~s/^\s+|\s+$//g;
		$U{message}=~s/\s+/ /g;
	}
	create_hotlinks();
	create_atnicks();
}

sub validate_post{# check if post would go through
	$U{delstatus}=$U{status};
	if($Q{sendto}[0]eq'*'){
		$U{poststatus}=GST;
		$U{displaysend}=$C{mesall};
		$U{displayrecp}=$I{seltoall};
	}
	elsif($Q{sendto}[0]eq'?'&&$U{status}>=REG){
		$U{poststatus}=REG;
		$U{displaysend}=$C{mesmem};
		$U{displayrecp}=$I{seltomem};
	}
	elsif($Q{sendto}[0]eq'#'&&$U{status}>=MOD){
		$U{poststatus}=MOD;
		$U{displaysend}=$C{messtaff};
		$U{displayrecp}=$I{seltoadm};
	}
	elsif($C{allowpms}){# known nick in room?
		foreach(keys%P){if($Q{sendto}[0]eq$P{$_}[0]and$U{nickname}ne$_){
			$U{recipient}=$_; 
			$U{displayrecp}=style_nick($_,$P{$_}[2]);
		}}
		if($U{recipient}){
			$U{poststatus}=SYS;
			$U{delstatus}=SYS;
			$U{displaysend}=$C{mespm};
		}
		else{# nick left already
			$Q{message}[0]='';
		}
	}
	else{# invalid recipient
		$Q{message}[0]='';
	}
}

sub formsafe{my$m="@_";
	$m=~s/&/&amp;/g;
	$m=~s/"/&quot;/g;
	$m=~s/</&lt;/g;
	$m=~s/>/&gt;/g;
	return $m;
}

sub htmlsafe{my$m="@_";
	$m=~s/&(?![\w\d\#]{2,10};)/&amp;/g;
	$m=~s/</&lt;/g;
	$m=~s/>/&gt;/g;
	$m=~s/"/&quot;/g;
	$m=~s/\r\n/<br>/g;
	$m=~s/\n/<br>/g;
	$m=~s/\r/<br>/g;
	return $m;
}

sub htmlactive{my$m="@_";
	$m=~s/&quot;/"/g;
	$m=~s/&lt;/</g;
	$m=~s/&gt;/>/g;
	$m=~s/&amp;/&/g;
	$m=~s/\r\n/\n/g;
	$m=~s/\r/\n/g;
	return $m;
}

sub create_atnicks{
	return if!$C{createatnicks}or$U{message}!~/\@/;
	my($f,$s,$e)=$U{sysmessage}?[]:get_fontinfo($U{fontinfo});
	my @list=sort{length($P{$b}[0])<=>length($P{$a}[0])}keys%P;#longest first, @Nicky vs. @Nick
	for(@list){my$n=rxsafe($_);$U{message}=~s/(^|\W)\@$n/$1.$e.$C{atnicksym}.style_nick($_,$P{$_}[2]).$s/ge}
	for(@list){my$n=rxsafe($_);$U{message}=~s/(^|\W)\@$n/$1.$e.$C{atnicksym}.style_nick($_,$P{$_}[2]).$s/gei}# @NICK vs. @nick
}

sub create_hotlinks{
	return if!$C{createlinks};
	#######################################################################################
	# Make hotlinks for URLs, redirect through dereferrer script to prevent session leakage
	#######################################################################################
	# 1. all explicit schemes with whatever xxx://yyyyyyy
	$U{message}=~s~((\w*://|\bmailto:)[^\s<>]+)~<<$1>>~ig;
	# 2. valid URLs without scheme (no IDNs yet!)
	$U{message}=~s~((?:[^\s<>]*:[^\s<>]*@)?(?:[a-z0-9\-]+\.)+[a-z]{2,}(?::\d*)?/[^\s<>]*)(?![^<>]*>)~<<$1>>~ig; # server/path given
	$U{message}=~s~((?:[^\s<>]*:[^\s<>]*@)?(?:\d{1,3}\.){3}\d{1,3}(?::\d*)?/[^\s<>]*)(?![^<>]*>)~<<$1>>~ig;     # 1.2.3.4/
	$U{message}=~s~((?:[^\s<>]*:[^\s<>]*@)?(?:[a-z0-9\-]+\.)+[a-z]{2,}:\d+)(?![^<>]*>)~<<$1>>~ig; # server:port given
	$U{message}=~s~([^\s<>]*:[^\s<>]*@(?:[a-z0-9\-]+\.)+[a-z]{2,}(?::\d+)?)(?![^<>]*>)~<<$1>>~ig; # au:th@server given
	# 3. likely servers without any hints but not filenames like *.rar zip exe etc. (no IDNs here yet!)
	$U{message}=~s~([a-z0-9\-]+(?:\.[a-z0-9\-]+)+(?:\.(?!rar|zip|exe|gz|7z|bat|doc)[a-z]{2,}))(?=[^a-z0-9\-\.]|$)(?![^<>]*>)~<<$1>>~ig;# xxx.yyy.zzz
	$U{message}=~s~(^|[^a-z0-9])((?:[a-z2-7]{56}|[a-z2-7]{16})\.onion)(?![^<>]*>)~$1<<$2>>~ig;# *.onion
	# @nicks could collide!
	$U{message}=~s~(^\@|\W\@)<<([^<>:]+)>>~$1$2~g if$C{createatnicks};
	# Convert every <<....>> into proper links:
	$U{message}=~s~<<([^<>]+)>>~url2hotlink($1)~ge;
	protect_tags($U{message});# protect links from atnicks
}

sub url2hotlink{
	# check for surrounding  < > " " ( ) etc. and create hotlink
	my($pre,$url,$app)=$_[0]=~/^((?:&(?:lt|gt|quot);)*)(.*?)((?:&(?:lt|gt|quot);|[\{\[\(\)\]\}])*)$/;
	my $id=($url=~/^mailto:/)?'email':'hotlink';
	return qq|$pre<a href="|.($C{useextderef}?$C{extderefurl}:$S).q|?action=redirect&amp;url=|.urlsafe($url).qq|" target="_blank" title="$url" id="$id">|.urlshort($url).qq|</a>$app|;
}

sub protect_tags{
	# protect stuff inside html tags, inserted by filters or hotlinks
	$_[0]=~s~(<(a|script|option|textarea|style)[\s>].*?</\2[^>]*>)~'<#'.he($1).'#>'~igse;# <x> .. </x>
	$_[0]=~s~(<[a-z0-9]+[\s]+([^"'>]+((["']).*?\4)?)+[^"'>]*?>)~'<#'.he($1).'#>'~ige;# <x ..>
}

sub unprotect_tags{$_[0]=~s~<#([a-f0-9]+)#>~hd($1)~ige}

sub urlsafe{my$u="@_";$u=~s/([\:\/\?\#\[\]\@\!\$\&\'\(\)\*\+\,\;\=\%])/sprintf("%%%02X",ord($1))/eg;$u}

sub urlshort{
	my$u="@_";
	return $u if($u=~s/^mailto://i);# email address
	# extract domain name
	$u=~s~^\w*:/+~~;
	$u=~s~[^\s]*:[^\s]*@~~;
	$u=~s~/.*$~~;
	$u=~s~:\d+$~~;
	if(length($u)>$C{maxlinklength}){# shorten long domains
		my$app=int($C{maxlinklength}/2);
		my$pre=$C{maxlinklength}-$app;
		$u=~s/(^.{$pre}).+(.{$app}$)/$1&hellip;$2/;
	}
	return $u;
}

sub add_user_message{
	return if''eq$U{message};
	my %newmessage=(
		postdate  =>$^T,
		postid    =>$U{postid},
		poststatus=>$U{poststatus},
		poster    =>$U{nickname},
		recipient =>$U{recipient},
		text      =>$C{mesbefore}.$U{displaysend}.style_this($U{message},$U{fontinfo}).$C{mesafter},
		delstatus =>$U{delstatus}
	);
	if($U{sysmessage}){# system PM
		$U{displaysend}=~s/<NICK>/$C{sysnick}/g;
		$C{sysbefore}=~s/<NICK>/$C{sysnick}/g;
		$C{sysafter}=~s/<NICK>/$C{sysnick}/g;
		$newmessage{text}=$C{sysbefore}.$U{displaysend}.$U{message}.$C{sysafter};
	}
	write_message(%newmessage);
}

sub add_staff_message{# system staff message (autokick from mod/admin) triggered
	return if''eq$U{message};
	$C{messtaff}=~s/<NICK>/$C{sysnick}/g;
	$C{mesbefore}=~s/<NICK>/$C{sysnick}/g;
	$C{mesafter}=~s/<NICK>/$C{sysnick}/g;
	$U{displayrecp}=$I{seltoadm};
	my %staffmessage=(
		postdate=>$^T,
		postid=>substr(rand(),-6),
		poststatus=>MOD,
		text=>$C{mesbefore}.$C{messtaff}.$U{message}.$C{mesafter},
		delstatus=>SYS
	);
	write_message(%staffmessage);
}

sub add_system_notification{
	return if''eq$_[0];
	$U{displayrecp}||=$I{seltoall};
	$C{sysbefore}=~s/<NICK>/$C{sysnick}/g;
	$C{sysafter}=~s/<NICK>/$C{sysnick}/g;
	$C{sysbefore}=~s/<RECP>/$I{seltoall}/g;
	$C{sysafter}=~s/<RECP>/$I{seltoall}/g;
	my %sysmessage=(
		postdate=>$^T,
		postid=>substr(rand(),-6),
		poststatus=>GST,
		text=>$C{sysbefore}.$_[0].$C{sysafter},
		delstatus=>SYS
	);
	write_message(%sysmessage);
}

sub write_message{my%message=@_;
	format_text($message{text});
	my @lines=open_file_rw(my$MESSAGES,'messages',my$ferr);send_error($ferr)if$ferr;
	while(my$line=shift@lines){
		my %temp=messagehash($line);
		print $MESSAGES $line unless expiredm($temp{postdate});
	}
	print $MESSAGES messageline(%message);
	$ferr=close_file($MESSAGES,'messages');send_error($ferr)if$ferr;
}

sub clean_room{
	$C{sysbefore}=~s/<NICK>/$C{sysnick}/g;
	$C{sysafter}=~s/<NICK>/$C{sysnick}/g;
	$C{sysbefore}=~s/<RECP>/$I{seltoall}/g;
	$C{sysafter}=~s/<RECP>/$I{seltoall}/g;
	$C{roomclean}=~s/<RECP>/$I{seltoall}/g;
	$C{roomclean}=~s/<NICK>/$C{sysnick}/g if$U{status}==SUP;
	my %sysmessage=(
		postdate=>$^T,
		postid=>substr(rand(),-6),
		poststatus=>GST,
		text=>$C{sysbefore}.$C{roomclean}.$C{sysafter},
		delstatus=>SYS
	);
	format_text($sysmessage{text});
	my $ferr=write_file('messages',messageline(%sysmessage));send_error($ferr)if$ferr;
}

sub clean_selected{
	my %mids;foreach(@{$Q{mid}}){$mids{$_}=1}
	my @lines=open_file_rw(my$MESSAGES,'messages',my$ferr);send_error($ferr)if$ferr;
	while(my $line=shift@lines){
		my %temp=messagehash($line);
		print $MESSAGES $line if!(expiredm($temp{postdate})||$mids{$temp{postdate}.$temp{postid}}&&($U{status}>$temp{delstatus}||$U{status}==MAD&&$temp{delstatus}==MAD));
	}
	$ferr=close_file($MESSAGES,'messages');send_error($ferr)if$ferr;
}

sub del_last_message{
	my $nick=$_[0];
	my @lines=open_file_rw(my$MESSAGES,'messages',my$ferr);send_error($ferr)if$ferr;
	for(my$i=@lines;$i>=0;$i--){
		my %temp=messagehash($lines[$i]);
		if($temp{poster}eq$nick){splice(@lines,$i,1);last}
	}
	while(my$line=shift@lines){
		my %temp=messagehash($line);
		print $MESSAGES $line if!expiredm($temp{postdate});
	}
	$ferr=close_file($MESSAGES,'messages');send_error($ferr)if$ferr;
}

sub del_all_messages{
	my $nick=$_[0];
	my @lines=open_file_rw(my$MESSAGES,'messages',my$ferr);send_error($ferr)if$ferr;
	while(my$line=shift@lines){
		my %temp=messagehash($line);
		print $MESSAGES $line if!(expiredm($temp{postdate})||$temp{poster}eq$nick);
	}
	$ferr=close_file($MESSAGES,'messages');send_error($ferr)if$ferr;
}

sub del_private_messages{
	my $nick=$_[0];
	my @lines=open_file_rw(my$MESSAGES,'messages',my$ferr);send_error($ferr)if$ferr;
	while(my$line=shift@lines){
		my %temp=messagehash($line);
		print $MESSAGES $line if!(expiredm($temp{postdate})||(''ne$nick&&$temp{poststatus}==SYS&&($temp{poster}eq$nick||$temp{recipient}eq$nick))||(''eq$nick&&$temp{poststatus}==SYS));
	}
	$ferr=close_file($MESSAGES,'messages');send_error($ferr)if$ferr;
}

sub print_messages{my $delstatus=$_[0];
	my @lines=slurp_file('messages',my$ferr);
	return if$ferr;
	while(my$line=pop@lines){
		my %message=messagehash($line);
		if($delstatus){# select messages to delete
			if($delstatus>$message{delstatus}||($delstatus==MAD&&$message{delstatus}==MAD)){
				print incheck('mid',$message{postdate}.$message{postid},0,$message{text}),'<br>'if!expiredm($message{postdate});
			}
		}
		elsif($U{status}>=$message{poststatus}||$U{nickname}eq$message{poster}||$U{nickname}eq$message{recipient}){ 
			print "$message{text}<br>"if!expiredm($message{postdate});  
		}
	}
}

######################################################################
# Superuser Setup
######################################################################

sub send_init{
	my $result=create_files();
	$I{setsuhelp}=~s/<DATA>/$datadir/;
	$I{nickhelp}=~s/<MAX>/$C{maxname}/;
	$I{passhelp}=~s/<MIN>/$C{minpass}/;
	print_start('setup');
	print "<center><h2>LE&nbsp;CHAT - $I{initsetup}</h2>";
	print form('','method="post"'),hidden('action','init'),qq|<table cellspacing="0" width="1"><tr><td align="center"><h3>$I{setsu}</h3></td></tr><tr><td align="center"><table cellspacing="0"><tr title="$I{nickhelp}"><td>$I{setsunick}</td><td>|,intext('sunick','15'),qq|</td></tr><tr title="$I{passhelp}"><td>$I{setsupass}</td><td>|,intext('supass','15'),qq|</td></tr><tr title="$I{passhelp}"><td>$I{setsupassconf}</td><td>|,intext('supassc','15'),qq|</td></tr></table><br><br></td></tr><tr><td align="left">$I{setsuhelp}<br><br><br></td></tr><tr><td align="center">|;
	print qq|<h3>$I{initback}</h3></td></tr><tr><td align="left">$I{initbackhelp}<br></td></tr><tr><td align="center">|,bakarea($result),'<br><br></td></tr><tr><td align="center"><br>',submit('initbut'),"</td></tr></table></form><br>$H{versiontag}</center>";
	print_end();
}

sub create_files{
	my $result='';
	# create directories if needed
	my @dirs=split('/',$datadir);my $dir='';
	while($_=shift@dirs){$dir.=$_;mkdir($dir,0700) unless -d$dir;$dir.='/'}
	chmod(0700,$datadir);
	# create files, keep existing ones
	create_file(qw(config members sessions messages waiting langedit));
	# check initial data in lechat.txt
	if(-e'./lechat.txt'){
		my $backupdata='';
		sysopen(my$LECHAT,'./lechat.txt',O_RDONLY) or return "$I{initlechattxt}\n$I{errfile} (lechat.txt/open)";
		flock($LECHAT,LOCK_SH) or return "$I{initlechattxt}\n$I{errfile} (lechat.txt/lock)";
		while(<$LECHAT>){$backupdata.=$_};
		close($LECHAT);
		$result=get_restore_results('',$backupdata);
		$result="$I{initlechattxt}\n$result";
		unlink('./lechat.txt');
		load_config();
	}
	return $result;
}

sub init_chat{
	$I{suerrbadnick}=~s/<MAX>/$C{maxname}/;
	$I{suerrbadpass}=~s/<MIN>/$C{minpass}/;
	# restore backups if given
	my $restore=$I{invalidbackup};
	$restore=get_restore_results()if$Q{backupdata}[0];
	# write superuser into "admin"
	my $suwrite;
	if(-e filepath('admin')){
		$suwrite=$I{suerrfileexist};
	}elsif(!valid_nick($Q{sunick}[0])){
		$suwrite=$I{suerrbadnick};
	}elsif(!allowed_pass($Q{supass}[0])){
		$suwrite=$I{suerrbadpass};
	}elsif($Q{supass}[0]ne$Q{supassc}[0]){
		$suwrite=$I{suerrbadpassc};
	}else{# all good data here
		$suwrite=write_admin(hash_this($Q{sunick}[0].hash_this($Q{sunick}[0]).hash_this($Q{supass}[0]).$Q{supass}[0]));
	}
	# Print results:
	print_start('setup');
	print "<center><h2>LE&nbsp;CHAT - $I{initsetup}</h2>",form(),hidden('action','setup'),hidden('nick',$Q{sunick}[0]),hidden('hexpass',he($Q{supass}[0])),qq|<table cellspacing="0" width="1"><tr><td align="center"><h3>$I{setsu}</h3></td></tr><tr><td align="center">$suwrite<br><br><br></td></tr><tr><td align="center"><h3>$I{initback}</h3></td></tr><tr><td align="center">|,bakarea($restore,1),'<br><br></td></tr><tr><td align="center"><br>',submit('initgotosetup'),"</td></tr></table></form><br>$H{versiontag}</center>";
	print_end();
}

sub write_admin{
	$I{suwritesucc}=~s/<DATA>/$datadir/g;
	$I{suwritefail}=~s/<DATA>/$datadir/g;
	write_file('admin',$_[0]);
	# read and verify data
	my($suverify)=slurp_file('admin');
	return $I{suwritesucc}if($_[0]eq$suverify);
	# delete again if not written correctly
	delete_file('admin');
	return $I{suwritefail};
}

sub change_admin_status{
	$I{errbadnick}=~s/<MAX>/$C{maxname}/;
	$I{errbadpass}=~s/<MIN>/$C{minpass}/;
	my $err;my %temp;
	return $I{errnonick}if!$Q{admnick}[0];
	return $I{errbaddata}if!$Q{what}[0]=~/^new|up|down$/;
	if($Q{what}[0]eq'new'){
		return $I{errbadnick}if!valid_nick($Q{admnick}[0]);
		return $I{errbadpass}if!allowed_pass($Q{admpass}[0]);
		$Q{admnick}[0]=he(cleanup_nick($Q{admnick}[0]));
	}
	my @lines=open_file_rw(my$MEMBERS,'members',my$ferr);send_error($ferr)if$ferr;
	foreach(@lines){
		%temp=memberhash($_);
		if(he($temp{nickname})eq$Q{admnick}[0]){
			if($Q{what}[0]eq'new'){$err=$I{errexistnick}}
			elsif($Q{what}[0]eq'up'){
				if($temp{status}==ADM){$temp{status}=MAD;$err=$I{raisemainsucc}}
				elsif($temp{status}==MAD){$err=$I{raisemaindone}}
				else{$err=$I{raisemainfail}}
			}
			elsif($Q{what}[0]eq'down'){   
				if($temp{status}==MAD){$temp{status}=ADM;$err=$I{lowerregsucc}}
				elsif($temp{status}==ADM){$err=$I{lowerregdone}}
				else{$err=$I{lowerregfail}}
			}
			print $MEMBERS memberline(%temp);
		}
		else{
			print $MEMBERS $_;
		}
		$err=~s/<RECP>/$temp{nickname}/ if $err;
	}
	if($Q{what}[0]eq'new'&&!$err){
		%temp=(nickname    =>hd($Q{admnick}[0]),
		       passhash    =>hash_this(hd($Q{admnick}[0]).$Q{admpass}[0]),
		       status      =>MAD,
		       colour      =>$C{coltxt});
		print $MEMBERS memberline(%temp);
		$err=$I{newmainreg};
		$err=~s/<RECP>/$temp{nickname}/;
	}
	$ferr=close_file($MEMBERS,'members');send_error($ferr)if$ferr;
	return $err;
}

######################################################################
# backup and restore
######################################################################

sub get_backup{my $fname=$_[0];
	my $finfo='langedit'eq$fname?'LANGUAGE':uc($fname);
	my $blob=join('n',slurp_file($fname,my$err)).'n';
	return $err if $err;
	my $fcomm=get_timestamp((stat(filepath($fname)))[9])." - $C{title}";
	$fcomm="Language: $I{languagename} ($I{languagecode}) - $version ($lastchanged)"if'language'eq$fname;
	$fcomm="Language: $L{languagename} ($L{languagecode}) - $version ($lastchanged)"if'langedit'eq$fname;
	$blob=~s/[^a-f0-9ln]//gi;
	$blob.='h'.hash_this($blob).'hi'.$finfo.'i';
	$blob="-----BEGIN LE CHAT $finfo-----\n$fcomm\n\n".encode_this($blob)."-----END LE CHAT $finfo-----";
	return $blob;
}

sub get_restore_results{my($fname,$bdata)=@_;
	$fname||='language config members';
	$bdata||=$Q{backupdata}[0];
	$bdata=~s/\r\n/<br>/g;
	$bdata=~s/\n/<br>/g;
	$bdata=~s/\r/<br>/g;
	$bdata=~s/<br>/\n/g;
	(my $conf)=$bdata=~/-----BEGIN LE CHAT CONFIG-----.*?\n\n(.*)-----END LE CHAT CONFIG-----/s;
	(my $memb)=$bdata=~/-----BEGIN LE CHAT MEMBERS-----.*?\n\n(.*)-----END LE CHAT MEMBERS-----/s;
	(my $lang)=$bdata=~/-----BEGIN LE CHAT LANGUAGE-----.*?\n\n(.*)-----END LE CHAT LANGUAGE-----/s;
	return $I{invalidbackup} unless($memb or $conf or $lang);
	my $result='';
	$result.=restore_file('langedit',$lang)."\n"if$fname=~/langedit/ and$lang;
	$result.=restore_file('language',$lang)."\n"if$fname=~/language/ and$lang;
	$result.=restore_file('config'  ,$conf)."\n"if$fname=~/config/   and$conf;
	$result.=restore_file('members' ,$memb)."\n"if$fname=~/members/  and$memb;
	return $result;
}

sub restore_file{my($fname,$fdata)=@_;
	my $finfo='langedit'eq$fname?'LANGUAGE':uc($fname);
	my $ftype=substr($fname,0,4);
	my $content=decode_this($fdata);
	my($blob,$hash,$info)=$content=~/^([a-f0-9ln]*)h([a-f0-9]+)hi([A-Z]+)i$/;
	if(hash_this($blob)eq$hash and $finfo eq $info){
		$blob=~tr/n/\n/s;
		my $ferror=write_file($fname,$blob);
		if($ferror){return $I{$ftype.'restfail'}.' '.$ferror}
		load_config();
		return $I{$ftype.'restsucc'};
	}
	else{
		return $I{$ftype.'restinval'};
	}
}

sub load_langedit{
	if(-e filepath('langedit')){
		my @lines=slurp_file('langedit',my$ferr);
		send_error($ferr)if$ferr;
		foreach(@lines){
			next unless /^[0-9a-f]/;
			my($lkey,$lval)=split('l',$_);
			$L{hd($lkey)}=hd($lval);
		}
	}
}

sub save_langedit{
	open_file_wo(my$LANG,'langedit',my$ferr);send_error($ferr)if$ferr;
	my $start=tell(DATA);
	while(<DATA>){
		my($ikey,$ival)=$_=~/^([a-z_]+)\s*=(.+)/i;
		next unless $ikey;
		$ival=$Q{"edit_$ikey"}[0]unless'stop_action'eq$ikey;
		$ival=~s/^\s*|\s*$//g;$ival=~s/\n//;$ival=~s/\r//;
		$ival=htmlactive($ival);
		print $LANG he($ikey),'l',he($ival),"l\n" if $ival;
	}
	seek(DATA,$start,0);
	$ferr=close_file($LANG,'langedit');send_error($ferr)if$ferr;
}

######################################################################
# file handling
######################################################################

sub filepath{($_[0]=~/^(members|guests)$/&&$D{membersdir}?$D{membersdir}:$datadir)."/$_[0]"}
sub create_file{foreach(@_){write_file($_)unless(-e filepath($_))}}
sub delete_file{foreach(@_){unlink(filepath($_))}}

sub get_guests_access{-s filepath('guestacc')||0}
sub get_chat_access{-s filepath('access')||0}

sub set_guests_access{
	return if($_[0]<FBD||$_[0]>ALL);
	write_file('guestacc','#'x$_[0]);
	cleanup_waiting_sessions()if$_[0]!=APP;
	$T{guests}=get_guests_access();
	rewrite_sessions();
}

sub set_chat_access{
	return if($_[0]<SUS||$_[0]>LNK);
	write_file('access','#'x$_[0]);
	$T{access}=get_chat_access();
	rewrite_sessions();
}

sub slurp_file{# name,error
	sysopen(my$FH,filepath($_[0]),O_RDONLY) or $_[1]="$I{errfile} ($_[0]/open)" and return;
	flock($FH,LOCK_SH) or $_[1]="$I{errfile} ($_[0]/lock)" and return;
	my @lines=<$FH>;
	close($FH) or $_[1]="$I{errfile} ($_[0]/close)" and return;
	$_[1]='';return @lines;
}

sub write_file{# name,text
	sysopen(my$FH,filepath($_[0]),O_WRONLY|O_TRUNC|O_CREAT,0600) or return "$I{errfile} ($_[0]/open)";
	flock($FH,LOCK_EX) or return "$I{errfile} ($_[0]/lock)";
	print $FH $_[1] or return "$I{errfile} ($_[0]/print)";
	close($FH) or return "$I{errfile} ($_[0]/close)";
	return '';
}

sub append_file{# name,text
	sysopen(my$FH,filepath($_[0]),O_WRONLY|O_APPEND|O_CREAT,0600) or return "$I{errfile} ($_[0]/open)";
	flock($FH,LOCK_EX) or return "$I{errfile} ($_[0]/lock)";
	print $FH $_[1] or return "$I{errfile} ($_[0]/print)";
	close($FH) or return "$I{errfile} ($_[0]/close)";
	return '';
}

sub open_file_rw{# FH,name,error
	sysopen($_[0],filepath($_[1]),O_RDWR|O_CREAT,0600) or $_[2]="$I{errfile} ($_[1]/open)" and return;
	flock($_[0],LOCK_EX) or $_[2]="$I{errfile} ($_[1]/lock)" and return;
	my $FH=$_[0];
	my @lines=<$FH>;
	seek($_[0],0,0) or $_[2]="$I{errfile} ($_[1]/seek)" and return;
	truncate($_[0],0) or $_[2]="$I{errfile} ($_[1]/truncate)" and return;
	$_[2]='';return @lines;
}

sub open_file_wo{# FH,name,error
	sysopen($_[0],filepath($_[1]),O_WRONLY|O_TRUNC|O_CREAT,0600) or $_[2]="$I{errfile} ($_[1]/open)" and return;
	flock($_[0],LOCK_EX) or $_[2]="$I{errfile} ($_[1]/lock)" and return;
	$_[2]='';
}

sub open_file_ro{# FH,name,error
	sysopen($_[0],filepath($_[1]),O_RDONLY) or $_[2]="$I{errfile} ($_[1]/open)" and return;
	flock($_[0],LOCK_SH) or $_[2]="$I{errfile} ($_[1]/lock)" and return;
	$_[2]='';
}

sub close_file{# FH,name
	close($_[0]) or return "$I{errfile} ($_[1]/close)";
	return '';
}

######################################################################
# data formats
######################################################################

sub guesthash{
	my @f=split('l',$_[0]);
	my %g=(
		status     =>GST,
		hex        =>   $f[0] ,
		nickname   =>hd($f[0]),
		passhash   =>   $f[1] ,
		refresh    =>hd($f[2]),
		colour     =>hd($f[3]),
		boxwidth   =>hd($f[4]),
		boxheight  =>hd($f[5]),
		expires    =>hd($f[6]),
	);
	return %g;
}

sub guestline{
	my %h=@_;
	my $g=
		he($h{nickname}   ).'l'.
		   $h{passhash}    .'l'.
		he($h{refresh}    ).'l'.
		he($h{colour}     ).'l'.
		he($h{boxwidth}   ).'l'.
		he($h{boxheight}  ).'l'.
		he($h{expires}    ).'l'.
		"\n";
	return $g;
}

sub memberhash{
	my @f=split('l',$_[0]);
	my %m=(
		hex         =>   $f[ 0] ,
		nickname    =>hd($f[ 0]),
		passhash    =>   $f[ 1] ,
		status      =>hd($f[ 2]),
		refresh     =>hd($f[ 3]),
		colour      =>hd($f[ 4]),
		fontface    =>hd($f[ 5]),
		fonttags    =>hd($f[ 6]),
		entryrefresh=>hd($f[ 7]),
		boxwidth    =>hd($f[ 8]),
		boxheight   =>hd($f[ 9]),
		frametop    =>hd($f[10]),
		framebottom =>hd($f[11]),
		exitdelpms  =>hd($f[12]),
	);
	#####################################################
	# preserve compatibility with existing memberfiles: #
	#####################################################
	   if($m{status}==0){$m{status}=ACD}                #
	elsif($m{status}==2){$m{status}=REG}                #
	elsif($m{status}==6){$m{status}=MOD}                #
	elsif($m{status}==7){$m{status}=ADM}                #
	elsif($m{status}==8){$m{status}=MAD}                #
	else                {$m{status}=REG}# just in case  #
	#####################################################
	return %m;
}

sub memberline{
	my %h=@_;
	#####################################################
	# preserve compatibility with existing memberfiles: #
	#####################################################
	   if($h{status}==ACD){$h{status}=0}                #
	elsif($h{status}==REG){$h{status}=2}                #
	elsif($h{status}==MOD){$h{status}=6}                #
	elsif($h{status}==ADM){$h{status}=7}                #
	elsif($h{status}==MAD){$h{status}=8}                #
	else                  {$h{status}=2}# just in case  #
	#####################################################
	my $m=
		he($h{nickname}    ).'l'.
		   $h{passhash}     .'l'.
		he($h{status}      ).'l'.
		he($h{refresh}     ).'l'.
		he($h{colour}      ).'l'.
		he($h{fontface}    ).'l'.
		he($h{fonttags}    ).'l'.
		he($h{entryrefresh}).'l'.
		he($h{boxwidth}    ).'l'.
		he($h{boxheight}   ).'l'.
		he($h{frametop}    ).'l'.
		he($h{framebottom} ).'l'.
		he($h{exitdelpms}  ).'l'.
		"\n";
	return $m;
}

sub sessionhash{
	my @f=split('l',$_[0]);  
	my %s=(
		postid      =>hd($f[ 0]),
		refresh     =>hd($f[ 1]),
		fontinfo    =>hd($f[ 2]),
		entryrefresh=>hd($f[ 3]),
		boxwidth    =>hd($f[ 4]),
		boxheight   =>hd($f[ 5]),
		nickname    =>hd($f[ 6]),
		hex         =>   $f[ 6] ,
		passhash    =>   $f[ 7] ,
		status      =>hd($f[ 8]),
		timestamp   =>hd($f[ 9]),
		ip          =>hd($f[10]),
		useragent   =>hd($f[11]),
		kickmessage =>hd($f[12]),
		frametop    =>hd($f[13]),
		framebottom =>hd($f[14]),
		exitdelpms  =>hd($f[15]),
		session     =>hd($f[16]),
	);
	return %s;
}

sub sessionline{
	my %h=@_;
	my $s= 
		he($h{postid}      ).'l'.
		he($h{refresh}     ).'l'.
		he($h{fontinfo}    ).'l'.
		he($h{entryrefresh}).'l'.
		he($h{boxwidth}    ).'l'.
		he($h{boxheight}   ).'l'.
		he($h{nickname}    ).'l'.
		   $h{passhash}     .'l'.
		he($h{status}      ).'l'.
		he($h{timestamp}   ).'l'.
		he($h{ip}          ).'l'.
		he($h{useragent}   ).'l'.
		he($h{kickmessage} ).'l'.
		he($h{frametop}    ).'l'.
		he($h{framebottom} ).'l'.
		he($h{exitdelpms}  ).'l'.
		he($h{session}     ).'l'.
		"\n";
	return $s;
}

sub captchahash{
	my @f=split('l',$_[0]);  
	my %h=(
		captchaid=>hd($f[0]),
		timestamp=>hd($f[1]),
		solution =>hd($f[2]),
		tempdata =>hd($f[3]),
		randseed =>hd($f[4]),
		session  =>hd($f[5]),
	);
	return %h;
}

sub captchaline{
	my %h=@_;
	my $l= 
		he($h{captchaid}).'l'.
		he($h{timestamp}).'l'.
		he($h{solution} ).'l'.
		he($h{tempdata} ).'l'.
		he($h{randseed} ).'l'.
		he($h{session}  ).'l'.
		"\n";
	return $l;
}

sub messagehash{
	my @f=split('l',$_[0]);  
	my %h=(
		postdate  =>hd($f[0]),
		postid    =>hd($f[1]),
		poststatus=>hd($f[2]),
		poster    =>hd($f[3]),
		recipient =>hd($f[4]),
		text      =>hd($f[5]),
		delstatus =>hd($f[6]),
	);
	return %h;
}

sub messageline{
	my %h=@_;
	my $l=
		he($h{postdate}  ).'l'.
		he($h{postid}    ).'l'.
		he($h{poststatus}).'l'.
		he($h{poster}    ).'l'.
		he($h{recipient} ).'l'.
		he($h{text}      ).'l'.
		he($h{delstatus} ).'l'.
		"\n";
	return $l;
}

######################################################################
# this and that
######################################################################

sub expiredm{($^T-$_[0]>60*$C{messageexpire})}
sub expireds{($^T-$_[0]>60*($_[1]>GST?$C{sessionexpire}:$C{guestsexpire}))}
sub expiredw{($^T-$_[0]>60*$C{waitingexpire})}
sub expiredc{($^T-$_[0]>60*$C{captchaexpire})}
sub valid_member_status{foreach(DEL,ACD,REG,MOD,ADM,MAD){return 1if$_[0]==$_}return}
sub valid_session_status{foreach(KCK,GST,REG,MOD,ADM,MAD){return 1if$_[0]==$_}return}
sub valid_waiting_status{foreach(WND,WNW,WNA){return 1if$_[0]==$_}return}
sub valid_splash_status{foreach(NEW,REG,MOD,ADM,MAD){return 1if$_[0]==$_}return}
sub valid_nick{!($_[0]=~/[^\w\d\s\(\)\[\]\{\}\=\/\-\!\@\#\$\%\?\+\*\^\.]/g||$_[0]!~/[a-z0-9]/i)}
sub allowed_nick{$_[0]=~/^.{1,$C{maxname}}$/}
sub allowed_pass{$_[0]=~/^.{$C{minpass},}$/}
sub similar_nick{my$x=lc($_[0]);my$y=lc($_[1]);$x=~y/a-z0-9//cd;$y=~y/a-z0-9//cd;$x eq $y?1:0}
sub cleanup_nick{my$n=$_[0];$n=~s/^\s+|\s+$//;$n=~s/\s+/ /g;$n}
sub hash_this{require Digest::MD5;Digest::MD5::md5_hex("@_")}
sub encode_this{require MIME::Base64;MIME::Base64::encode_base64($_[0])}
sub decode_this{require MIME::Base64;MIME::Base64::decode_base64($_[0])}
sub he{unpack('H*',$_[0])} sub hd{pack('H*',$_[0])}# hex-encode/decode
sub get_time{substr(get_timestamp($_[0]),-8,8)}
sub get_date{substr(get_timestamp($_[0]),0,10)}
sub gmtoff{my$o=$_[0]||$C{gmtoffset};$o=substr($o,0,1).((substr($o,1,2)*60+substr($o,3,2))*60);$^T+$o}
sub get_timestamp{my($sec,$min,$hour,$day,$mon,$year)=gmtime($_[0]||$^T);$year+=1900;$mon++;foreach($sec,$min,$hour,$day,$mon){$_=substr('0'.$_,-2,2)}return"$year-$mon-$day $hour:$min:$sec"}

sub get_timeout{# lastpost, status
	my $s=$_[0]+(60*($_[1]>GST?$C{sessionexpire}:$C{guestsexpire}))-$^T;
	my $m=int($s/60);$s-=$m*60;
	my $h=int($m/60);$m-=$h*60;
	$s=substr('0'.$s,-2,2);
	$m=substr('0'.$m,-2,2)if$h;
	return$h?"$h:$m:$s":"$m:$s";
}

sub print_colours{
	# Prints a short list with selected named HTML colours and filters out illegible text colours for the given background.
	# It's a simple comparison of weighted grey values. This is not very accurate but gets the job done well enough.
	# If you want more accuracy, do some research about "Delta E", though the serious math involved there is not worth the effort just for this here I guess. ;)
	my %colours=($I{Beige}=>'F5F5DC',$I{Black}=>'000000',$I{Blue}=>'0000FF',$I{BlueViolet}=>'8A2BE2',$I{Brown}=>'A52A2A',$I{Cyan}=>'00FFFF',$I{DarkBlue}=>'00008B',$I{DarkGreen}=>'006400',$I{DarkRed}=>'8B0000',$I{DarkViolet}=>'9400D3',$I{DeepSkyBlue}=>'00BFFF',$I{Gold}=>'FFD700',$I{Grey}=>'808080',$I{Green}=>'008000',$I{HotPink}=>'FF69B4',$I{Indigo}=>'4B0082',$I{LightBlue}=>'ADD8E6',$I{LightGreen}=>'90EE90',$I{LimeGreen}=>'32CD32',$I{Magenta}=>'FF00FF',$I{Olive}=>'808000',$I{Orange}=>'FFA500',$I{OrangeRed}=>'FF4500',$I{Purple}=>'800080',$I{Red}=>'FF0000',$I{RoyalBlue}=>'4169E1',$I{SeaGreen}=>'2E8B57',$I{Sienna}=>'A0522D',$I{Silver}=>'C0C0C0',$I{Tan}=>'D2B48C',$I{Teal}=>'008080',$I{Violet}=>'EE82EE',$I{White}=>'FFFFFF',$I{Yellow}=>'FFFF00',$I{YellowGreen}=>'9ACD32');
	my $greybg=greyval($C{colbg});
	foreach(sort keys %colours){
		print qq|<option value="$colours{$_}" style="color:#$colours{$_}">$_</option>|unless(abs($greybg-greyval($colours{$_}))<75);
	}
}

sub greyval{hex(substr($_[0],0,2))*.3+hex(substr($_[0],2,2))*.59+hex(substr($_[0],4,2))*.11}

sub get_fontinfo{my($styleinfo,$restrict)=@_;
	(my $fbold)=$styleinfo=~/(<i?bi?>|:bold)/;
	(my $fitalic)=$styleinfo=~/(<b?ib?>|:italic)/;
	(my $fsmall)=$styleinfo=~/(size="-1"|:smaller)/;
	(my $fcolour)=$styleinfo=~/(#.{6})/;
	(my $fface)=$styleinfo=~/face="([^"]+)"/;
	(my $sface)=$styleinfo=~/font-family:([^;]+);/;
	if($fface ne ''){$sface=$fface;$sface=~s/^/'/;$sface=~s/$/'/;$sface=~s/,/','/g}
	else{$fface=$sface;$fface=~s/'//}
	my $fstyle='';
	$fstyle.="color:$fcolour;"if$fcolour;
	if(!$restrict||$C{allowfonts}){
		$fstyle.="font-family:$sface;"if$sface;
		$fstyle.='font-size:smaller;'if$fsmall;
		$fstyle.='font-weight:'.($fbold?'bold;':'normal;');
		$fstyle.='font-style:'.($fitalic?'italic;':'normal;');
	}
	my $fstart='<font';
	$fstart.=qq| color="$fcolour"|if$fcolour;
	if(!$restrict||$C{allowfonts}){
		$fstart.=qq| face="$fface"|if$fface;
		$fstart.=qq| size="-1"|if$fsmall;
		$fstart.=qq| style="$fstyle"|if$fstyle;
	}
	$fstart.='>';
	if(!$restrict||$C{allowfonts}){
		$fstart.='<b>'if$fbold;
		$fstart.='<i>'if$fitalic;
	}
	my $fend='';
	if(!$restrict||$C{allowfonts}){
		$fend.='</i>'if$fitalic;
		$fend.='</b>'if$fbold;
	}
	$fend.='</font>';
	return ($fstyle,$fstart,$fend);
}
sub get_style{my($f)=get_fontinfo($_[0],1);return$f}
sub style_this{my($text,$font)=@_;my($f,$s,$e)=get_fontinfo($font,1);return"$s$text$e"}
sub style_nick{return '<span class="chatter nick_'.he($_[0]).'">'.style_this(format_nick($_[0],$_[2]),$_[1]).'</span>'}

sub format_nick{my($name,$stat)=@_;
	$name=~s/\s+/&nbsp;/g;
	$name.=($stat==REG?'':'&nbsp;'.($stat==KCK||$stat==ACD?$I{symdenied}:$stat==GST?$I{symguest}:$stat==MOD?$I{symmod}:$stat>=ADM?$I{symadmin}:''))if$stat;
	return $name;
}

sub format_info{
	my $info=qq|<small><table class="placeholders"><thead><tr><th colspan="4" align="left">$I{placeholders}</th></tr></thead><tbody valign="top">|;my $tr=1;
	foreach(qw(CHAT ALL NICK ALLNUM RECP GUESTS IP GUESTSNUM RULES MEMBERS HELP MEMBERSNUM ADDHELP STAFF TIME STAFFNUM DATE VER)){
		$info.='<tr>'if$tr;
		$info.=qq|<td align="left" class="$_">&nbsp;&#60;$_&#62;&nbsp;</td><td align="left" class="$_">$I{$_}</td>|;
		$info.='</tr>'if!$tr;$tr=1-$tr;
	}
	$info.=qq|<tr class="whitespaceinfo"><td colspan="4" align="left">$I{whitespaceinfo}</td></tr></tbody></table></small>|;
}

sub format_text{
	protect_tags($_[0]);
	foreach($_[0]){if(!/<(br|p|td).*?>/i){s/\r\n/<br>/g;s/\n/<br>/g;s/\r/<br>/g}}
	$_[0]=~s/<NICK>/$U{displayname}/g;
	$_[0]=~s/<RECP>/$U{displayrecp}/g;
	$_[0]=~s/<ALL>/join(' &nbsp; ',(@M,@G))/eg;
	$_[0]=~s/<ALLNUM>/@M+@G/eg;
	$_[0]=~s/<GUESTS>/join(' &nbsp; ',@G)/eg;
	$_[0]=~s/<GUESTSNUM>/@G/eg;
	$_[0]=~s/<MEMBERS>/join(' &nbsp; ',@M)/eg;
	$_[0]=~s/<MEMBERSNUM>/@M/eg;
	$_[0]=~s/<STAFF>/join(' &nbsp; ',@S)/eg;
	$_[0]=~s/<STAFFNUM>/@S/eg;
	$_[0]=~s/<HELP>/helptext()/eg;
	$_[0]=~s/<ADDHELP>/addhelptext()/eg;
	$_[0]=~s/<RULES>/rulestext()/eg;
	$_[0]=~s/<TIME([+-]\d{4})?>/get_time(gmtoff($1))/eg;
	$_[0]=~s/<DATE([+-]\d{4})?>/get_date(gmtoff($1))/eg;
	$_[0]=~s/<IP>/$ENV{REMOTE_ADDR}/g;
	$_[0]=~s/<VER>/$H{versiontag}/g;
	$_[0]=~s/<CHAT>/$C{title}/g;
	unprotect_tags($_[0]);
	return $_[0];
}

sub rulestext{$C{rulestxt}=~s/<RULES>//g;format_text($C{rulestxt})}
sub helptext{($U{status}>=GST?"$I{helpguests}<br><br>":'').($U{status}>=REG?"$I{helpregs}<br><br>":'').($U{status}>=MOD?"$I{helpmods}<br><br>":'').($U{status}>=ADM?"$I{helpadmins}<br><br>":'')}
sub addhelptext{($U{status}>=GST&&$C{addhelpgst}?format_text($C{addhelpgst}).'<br><br>':'').($U{status}>=REG&&$C{addhelpreg}?format_text($C{addhelpreg}).'<br><br>':'').($U{status}>=MOD&&$C{addhelpmod}?format_text($C{addhelpmod}).'<br><br>':'').($U{status}>=ADM&&$C{addhelpadm}?format_text($C{addhelpadm}).'<br><br>':'')}

######################################################################
# configuration, defaults and internals
######################################################################

sub load_config{
	$Q{noframes}[0]=''if$Q{noframes}[0]&&$Q{action}[0]eq'logout';# get rid of hidden form field
	set_internal_defaults();
	my($ferr,$fkey,$fval);
	if(-e filepath('language')){# load language file
		open_file_ro(my$LANG,'language',$ferr);send_fatal($ferr)if$ferr;
		while(<$LANG>){
			next unless /^[0-9a-f]/;
			($fkey,$fval)=split('l',$_);
			$fkey=hd($fkey);
			$fval=hd($fval);
			last if('stop_action'eq$fkey&&$fval=~/-$Q{action}[0]-/o);# only load what we need
			$I{$fkey}=$fval;
		}
		$ferr=close_file($LANG,'language');send_fatal($ferr)if$ferr;
	}
	if(-e filepath('dirs')){# captcha+shared members?
		open_file_ro(my$DIRS,'dirs',$ferr);send_fatal($ferr)if$ferr;
		while(<$DIRS>){
			next unless /^[0-9a-f]/;
			($fkey,$fval)=split('l',$_);
			$fkey=hd($fkey);
			$fval=hd($fval);
			$D{$fkey}=$fval;
		}
		$ferr=close_file($DIRS,'dirs');send_fatal($ferr)if$ferr;
	}
	set_config_defaults();
	open_file_ro(my$CONFIG,'config',$ferr);send_fatal($ferr)if$ferr;
	while(<$CONFIG>){
		next unless /^[0-9a-f]/;
		($fkey,$fval)=split('l',$_);
		$fkey=hd($fkey);
		$fval=hd($fval);
		last if('stop_action'eq$fkey&&$fval=~/-$Q{action}[0]-/o);# only load what we need
		$C{$fkey}=$fval;
	}
	$ferr=close_file($CONFIG,'config');send_fatal($ferr)if$ferr;
	set_html_vars();
	$T{guests}=get_guests_access();# guest settings
	$T{access}=get_chat_access();# suspended?
}

sub set_directories{
	# check if valid or reset to empty
	foreach(qw(membersdir captchalibdir captchaimgdir)){$D{$_}=htmlactive($Q{$_}[0]);$D{$_}=~s/^\s+|\s+$//g;$D{$_}=''if!-d$D{$_};$C{$_}=$D{$_};}
	# check file readability
	slurp_file('members',my$ferr);
	if($ferr){$D{membersdir}='';$C{membersdir}=''}
}

sub save_directories{
	set_chat_access(0);
	clean_room();
	open_file_wo(my$DIRS,'dirs',my$ferr);send_error($ferr)if$ferr;
	foreach(qw(membersdir captchalibdir captchaimgdir)){print $DIRS he($_),'l',he($D{$_}),"l\n"}
	$ferr=close_file($DIRS,'dirs');send_error($ferr)if$ferr;
}

sub save_config{
	open_file_wo(my$CONFIG,'config',my$ferr);send_error($ferr)if$ferr;
	foreach(qw(redirifsusp redirtourl title favicon kickederror coltxt colbg collnk colvis colact sessionexpire guestsexpire messageexpire guestspreserve kickpenalty waitingexpire hideguests defaultrefresh minrefresh maxrefresh maxmessage maxname minpass floodlimit boxwidth boxheight allowmultiline allowfonts allowpms autocleanup keepguests cssglobal styleback csserror cssview cssnote styletoplist csswait stylecheckwait stylewaitrel roomentry entrymessage useextderef showdisclaimer disclaimer createlinks maxlinklength createatnicks atnicksym csscontrols stylerelpost stylerelmes stylepause styleprofile styleadmin stylerules styleexit insideheader insidefooter gmtoffset rulestxt addhelpgst addhelpreg addhelpmod addhelpadm frametopdef framebottomdef sysbefore sysafter))
		{print $CONFIG he($_),'l',he($C{$_}),"l\n"}print $CONFIG he('stop_action'),'l',he('-view-wait-redirect-colours-controls-'),"l\n";
	foreach(qw(mesall mesmem messtaff mespm mesbefore mesafter sysnick csspost styleposttext stylepostsend stylesendlist styledellast styledelall styleswitch extderefurl textfilters kickedmessage cssprofile))
		{print $CONFIG he($_),'l',he($C{$_}),"l\n"}print $CONFIG he('stop_action'),'l',he('-post-delete-profile-'),"l\n";
	foreach(qw(header footer noguests nomembers rndguestcol loginbutton csslogin stylelogintext stylecolselect styleenter captchaexpire captchause captchaall captchamodule splashshow splashall splashtxt splashcnt csssplash stylesplashcnt cssrules roomexit logoutmessage roomclean))
		{print $CONFIG he($_),'l',he($C{$_}),"l\n"}print $CONFIG he('stop_action'),'l',he('--splash-captcha-login-chat-help-logout-'),"l\n";
	foreach(qw(regmessage styledelsome cssadmin csssetup lastchangedby lastchangedat))
		{print $CONFIG he($_),'l',he($C{$_}),"l\n"}
	$ferr=close_file($CONFIG,'config');send_error($ferr)if$ferr;
	rewrite_sessions();
}

sub set_config{
	foreach(keys %C){$C{$_}=htmlactive($Q{$_}[0]);$C{$_}=~s/^\s+|\s+$//g;}
	$C{textfilters}=filters_from_queries();
	$C{lastchangedby}=$U{nickname};
	$C{lastchangedat}=get_timestamp();
	check_config();
	set_html_vars();
}

sub check_config{
	# Revert to defaults if invalid or empty
	foreach(qw(colbg coltxt collnk colvis colact)){$C{$_}=''if$C{$_}!~/^[a-f0-9]{6}$/i}
	$C{colbg} ||='000000';
	$C{coltxt}||='FFFFFF';
	$C{collnk}||='6666FF';
	$C{colvis}||='FF66FF';
	$C{colact}||='FF0033';
	foreach(qw(maxlinklength sessionexpire guestsexpire messageexpire waitingexpire guestspreserve hideguests kickpenalty defaultrefresh minrefresh maxrefresh maxmessage maxname minpass floodlimit boxwidthdef boxheightdef)){$C{$_}=~y/0-9//cd;$C{$_}=~s/^0+//}
	foreach(qw(frametopdef framebottomdef)){$C{$_}=~y/0-9%//cd;$C{$_}=~s/^0+|%(?!$)//g}
	$C{sessionexpire} ||='15';
	$C{guestsexpire}  ||='10';
	$C{messageexpire} ||='20';
	$C{kickpenalty}   ||='10';
	$C{captchaexpire} ||='10';
	$C{waitingexpire} ||='10';
	$C{guestspreserve}||='24';
	$C{hideguests}    ||='10';
	$C{defaultrefresh}||='20';
	$C{minrefresh}    ||='10'; $C{minrefresh}=$C{defaultrefresh}if$C{minrefresh}>$C{defaultrefresh};
	$C{maxrefresh}    ||='180';$C{maxrefresh}=$C{defaultrefresh}if$C{maxrefresh}<$C{defaultrefresh};
	$C{maxmessage}    ||='1000';
	$C{maxname}       ||='30';
	$C{minpass}       ||='10';
	$C{floodlimit}    ||='1';
	$C{boxwidthdef}   ||='50';
	$C{boxheightdef}  ||='3';
	$C{frametopdef}   ||='180';
	$C{framebottomdef}||='90';
	$C{maxlinklength}='22'if''eq$C{maxlinklength};
	$C{gmtoffset}=''if$C{gmtoffset}!~/^[+-]\d{4}$/;
	# Use language defaults if emptied
	$C{title}||='LE CHAT';
	$C{sysnick}||='<CHAT>';
	foreach(qw(header footer disclaimer noguests nomembers loginbutton rulestxt entrymessage logoutmessage kickederror roomentry roomexit regmessage kickedmessage roomclean mesall mesmem mespm messtaff splashtxt splashcnt)){$C{$_}||=$I{"c$_"}}
	# remove circular references
	foreach(qw(rulestxt addhelpgst addhelpreg addhelpmod addhelpadm)){$C{$_}=~s/<RULES>|<ADDHELP>//g}
	# add dirs for superuser setup and use in captcha modules
	foreach(qw(membersdir captchalibdir captchaimgdir)){$C{$_}=$D{$_}}
}

sub set_config_defaults{
	# define/reset keys
	%C=();foreach(qw(lastchangedby lastchangedat redirifsusp redirtourl createlinks maxlinklength createatnicks atnicksym useextderef extderefurl showdisclaimer allowmultiline allowfonts allowpms title favicon header footer insideheader insidefooter disclaimer noguests nomembers loginbutton rulestxt addhelpgst addhelpreg addhelpmod addhelpadm entrymessage logoutmessage kickederror roomentry roomexit regmessage kickedmessage roomclean sysnick mesall mesmem mespm messtaff captchaexpire captchause captchaall captchaimgdir captchalibdir captchamodule splashshow splashall splashtxt splashcnt csssplash stylesplashcnt textfilters rndguestcol autocleanup keepguests guestspreserve sessionexpire guestsexpire messageexpire kickpenalty waitingexpire hideguests defaultrefresh minrefresh maxrefresh maxmessage maxname minpass floodlimit boxwidthdef boxheightdef coltxt colbg collnk colvis colact cssglobal styleback cssview styletoplist styledelsome stylecheckwait csswait stylewaitrel csspost styleposttext stylepostsend stylesendlist styledellast styledelall styleswitch csscontrols stylerelpost stylerelmes stylepause styleprofile styleadmin stylerules styleexit csslogin stylelogintext stylecolselect styleenter csserror cssprofile cssrules cssnote cssadmin csssetup frametopdef framebottomdef gmtoffset)){$C{$_}=''}
	# initial defaults
	$C{lastchangedby}='-';
	$C{lastchangedat}='-';
	$C{createlinks}='1';
	$C{maxlinklength}='22';
	$C{createatnicks}='1';
	$C{atnicksym}='<small><sup>@</sup></small>';
	$C{allowmultiline}='1';
	$C{allowfonts}='1';
	$C{allowpms}='1';
	$C{rndguestcol}='1';
	$C{autocleanup}='1';
	$C{keepguests}='1';
	$C{guestspreserve}='24';
	$C{textfilters}=$I{ctextfilters};
	$C{favicon}='data:image/gif;base64,R0lGODlhEAAQALMAAP///wAAAEBAQICAgAAAgIAAgACAgMDAwICAgP8AAAD/AP//AAAA//8A/wD//////ywAAAAAEAAQAAAEPBAMQGW9dITB9cSVFoxBOH4SuWWbx5KTa5lrimKyDOp6KKK9FMx0Ew1ZF+Pp01PWmqoVpyaMHjOdbKcSAQA7';
	$C{cssglobal}="input,select,textarea{color:#FFFFFF;background-color:#000000;}\nbody,div.bar{background-image:url(data:image/gif;base64,R0lGODdhCAAIALMAAAAAADMzMwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwAAAAACAAIAAAEChDISQO9OOu6dwQAOw==);}";
	$C{styleback}='background-color:#004400;color:#FFFFFF;';
	$C{styledelsome}='background-color:#660000;color:#FFFFFF;';
	$C{stylecheckwait}='background-color:#660000;color:#FFFFFF;';
	$C{stylecolselect}='text-align:center;';
	$C{csserror}='body{color:#FF0033;}';
	$C{csssetup}='.regexerror{color:#FF0000;}';
	# required defaults
	check_config();
}

sub set_internal_defaults{
	%F=(# fonts. TODO: review these and choose some cross-platform friendly items
		'Arial'          =>' face="Arial,Helvetica,sans-serif"',
		'Book Antiqua'   =>' face="Book Antiqua,MS Gothic"',
		'Comic'          =>' face="Comic Sans MS,Papyrus"', 
		'Comic small'    =>' face="Comic Sans MS,Papyrus" size="-1"',
		'Courier'        =>' face="Courier New,Courier,monospace"',
		'Cursive'        =>' face="Cursive,Papyrus"',
		'Fantasy'        =>' face="Fantasy,Futura,Papyrus"',
		'Garamond'       =>' face="Garamond,Palatino,serif"',
		'Georgia'        =>' face="Georgia,Times New Roman,Times,serif"',
		'Serif'          =>' face="MS Serif,New York,serif"',
		'System'         =>' face="System,Chicago,sans-serif"',
		'Times New Roman'=>' face="Times New Roman,Times,serif"',
		'Verdana'        =>' face="Verdana,Geneva,Arial,Helvetica,sans-serif"',
		'Verdana small'  =>' face="Verdana,Geneva,Arial,Helvetica,sans-serif" size="-1"'
	);
	# Load default internal messages from __DATA__
	my $start=tell(DATA);
	while(<DATA>){
		my($ikey,$ival)=$_=~/^([a-z_]+)\s*=(.+)/i;
		next unless $ikey;
		last if('stop_action'eq$ikey&&$ival=~/-$Q{action}[0]-/o);# only load what we need
		$I{$ikey}=$ival;
	}
	seek(DATA,$start,0);# rewind for second use (language editing)
}

sub set_html_vars{
	%H=(# default HTML
		# Don't change the encoding or existing member passes with special characters will break! 
		# Maybe I'll finally switch to utf-8 some time in the future and open that Pandoras box...
		encoding     =>'iso-8859-1',
		begin_body   =>qq|\n<body bgcolor="#$C{colbg}" text="#$C{coltxt}" link="#$C{collnk}" alink="#$C{colact}" vlink="#$C{colvis}" class="chat">\n|,
		end_body     =>"\n</body>",
		end_html     =>"\n</html>\n\n",
		method       =>'method="post"',
		add_css      =>'',# can be used for banner-killers below
		versiontag   =>"<small>LE&nbsp;CHAT&nbsp;-&nbsp;$version</small>",
		versioncom   =>"<!-- LE CHAT $version ($lastchanged) Original script source available at: http://4fvfamdpoulu2nms.onion/lechat/ -->",# please keep this!
		);%H=(%H,
		begin_html   =>qq|\n<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">\n$H{versioncom}\n<html>\n|,
		begin_frames =>qq|\n<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Frameset//EN" "http://www.w3.org/TR/html4/frameset.dtd">\n$H{versioncom}\n<html>\n|,
		meta_html    =>qq|\n<title>$C{title}</title>\n|.linkrel($C{favicon}).qq|<meta name="robots" content="noindex,nofollow">\n<meta name="referrer" content="no-referrer">\n<meta http-equiv="Content-Type" content="text/html; charset=$H{encoding}">\n<meta http-equiv="Content-Language" content="$I{languagecode}">\n<meta http-equiv="Pragma" content="no-cache">\n<meta http-equiv="expires" content="0">\n<meta http-equiv="Content-Security-Policy" content="referrer no-referrer;">\n|,
		backtologin  =>form('_parent').submit('backtologin','styleback').'</form>',
		backtochat   =>form().hidden('action','view').hidden('session',$Q{session}[0]).submit('backtochat','styleback').'</form>',
		backtoprofile=>form().hidden('action','profile').hidden('session',$Q{session}[0]).submit('backtoprofile','styleback').'</form>',
		backtosetup  =>form().hidden('action','setup').hidden('nick',$Q{nick}[0]).hidden('hexpass',$Q{hexpass}[0]||he($Q{pass}[0])).submit('backtosetup','styleback').'</form>',
	);
	##################################################################
	# Banner killers and other corrections for known servers. If you #
	# add your own, consider sending me a copy for the script, if it #
	# may be useful for others. Or tell me your favourite freehosts! #
	##################################################################
	if($ENV{SERVER_NAME}=~m/\.onion$/){
		$ENV{REMOTE_ADDR}=$I{unknownip};# there are no IPs in Torland ;)
		if($ENV{HTTP_X_TOR2WEB}||$ENV{HTTP_X_REAL_IP}){# ..unless you don't use Tor yourself!!
			if($Q{noframes}[0]||$Q{action}[0]!~/^(view|controls|admin|profile|colours|help)$/){
				$ENV{REMOTE_ADDR}=$ENV{HTTP_X_REAL_IP};
				$ENV{REMOTE_ADDR}||=$ENV{HTTP_X_FORWARDED_FOR};
				$ENV{REMOTE_ADDR}||=$I{unknownip};
				$I{proxywarning}=~s~<TORBROWSER>~<a href="https://www.torproject.org/" class="warn" style="color:red;text-decoration:underline;">Tor Browser</a>~g;
				$H{begin_body}.=qq|<div class="warn" style="position:fixed;left:0;top:0;display:block;min-width:100%;max-width:100%;min-height:1.5em;overflow:visible;margin:0;padding:0.5em;background:lightyellow;color:red;z-index:9999999999;"><hr style="display:none;"><b>$I{proxywarning}</b><hr style="display:none;"></div><div style="position:static;display:block;min-height:1.5em;margin:0;padding:0.5em;background:transparent;"><br></div>|;
			}
		}
	}
	elsif($ENV{SERVER_NAME}=~m/\.atpages\.jp$/){
		$H{begin_body}.='<div style="display:block;width:98%;height:98%;max-width:98%;max-height:98%;position:absolute;top:0;left:0;padding:1%;z-index:9999999998;overflow:visible;">';
		$H{end_body}='<noembed><noframes><xml><xmp>'.$H{end_body};
		foreach(qw(method backtologin backtochat backtoprofile backtosetup)){$H{$_}=~s/method="post"/method="get"/}# large IP-bans on POST requests
	}
	elsif($ENV{SERVER_NAME}=~m/\.tok2\.com$/){
		$H{begin_body}='<noembed><noscript><body></noscript></noembed>'.$H{begin_body};
		$H{end_body}='<noembed><noscript>'.$H{end_body};
		$ENV{REMOTE_ADDR}=$ENV{HTTP_X_FORWARDED_FOR}if($ENV{REMOTE_ADDR}eq$ENV{SERVER_ADDR}and$ENV{HTTP_X_FORWARDED_FOR});# fix for some misconfigured tok2-servers
	}
	elsif($ENV{SERVER_NAME}=~m/\.h(ut)?\d+?\.ru$/){
		$H{end_html}.='<div style="display:none"><noembed><xml><xmp>';
	}
	elsif($ENV{SERVER_NAME}=~m/\.fatal\.ru$/){
		$H{end_body}='<div style="display:none"><noembed><xml><xmp><!--'.$H{end_body};
	}
}

######################################################################
# cgi stuff
######################################################################
sub GetQuery{read(STDIN,my$q,$ENV{CONTENT_LENGTH}||0);QueryHash($q)}
sub GetParam{QueryHash($ENV{QUERY_STRING}||'')}
sub QueryHash{my($n,$v,%h);foreach(split(/&|;/,$_[0]||'')){($n,$v)=split(/=/,$_);$v=~tr/+/ /;$v=~s/%([\dA-Fa-f]{2})/pack('C',hex($1))/eg;$h{$n}||=[];push@{$h{$n}},$v}return%h}
sub GetScript{$0=~/([^\\\/]+)$/;$1||die}

######################################################################
# Internal messages. Don't edit here, use the setup-page as superuser
# and create a language file. If you want to share, send me a copy! :)
######################################################################
__DATA__
languagename=English
languagecode=en-gb
# login page
nickname     =Nickname:
password     =Password:
nickhelp     =<MAX> characters maximum, no special characters allowed
passhelp     =at least <MIN> characters required
selcolguests =New guests, choose a good password and a colour:
selcoldefault=Room Default
selcolrandom =Random Colour
unknownip    =not available
proxywarning =Warning! Tor2web-proxy detected! For your own safety please download and use <TORBROWSER> to surf onion-sites!
# colour names
Beige      =beige
Black      =black
Blue       =blue
BlueViolet =blue violet
Brown      =brown
Cyan       =cyan
DarkBlue   =dark blue
DarkGreen  =dark green
DarkRed    =dark red
DarkViolet =dark violet
DeepSkyBlue=sky blue
Gold       =gold
Grey       =grey
Green      =green
HotPink    =hot pink
Indigo     =indigo
LightBlue  =light blue
LightGreen =light green
LimeGreen  =lime green
Magenta    =magenta
Olive      =olive
Orange     =orange
OrangeRed  =orange red
Purple     =purple
Red        =red
RoyalBlue  =royal blue
SeaGreen   =sea green
Sienna     =sienna
Silver     =silver
Tan        =tan
Teal       =teal
Violet     =violet
White      =white
Yellow     =yellow
YellowGreen=yellow green
# link redirects
linkredirect=Redirecting to:
linknonhttp =Non-http link requested:
linktryhttp =Try link as http:
errnolinks  =Link redirection is disabled.
# suspended page
suspended=Suspended
susptext =This chat is currently not available. Please try again later!
redirtext=Please try this alternate address!
# error messages
fatalerror  =Fatal Error!
error       =Error:
errfile     =file error
errmodule   =module error
errexpired  =invalid/expired session
erraccdenied=access denied
errnoguests =no guests allowed at this time
errnomembers=only staff allowed at this time
errnocaptcha=CAPTCHA module not found.
backtologin =Back to the login page.
# messages frame
members     =Members:
guests      =Guests:
butcheckwait=Check <COUNT> Newcomer(s)
navbottom   =bottom
navtop      =top
# config default text
cheader       =<h1><CHAT></h1>Your IP address is <IP><br><br>
cfooter       =Currently <ALLNUM> chatter(s) in room:<br><ALL><br><br><VER>
cnoguests     =Only members at this time!
cnomembers    =Only staff at this time!
cloginbutton  =Come in!
crulestxt     =Just be nice!
csplashtxt    =<h2>Hello <NICK>!</h2>Please follow the chat rules:<br><br><RULES><br>
csplashcnt    =continue
cinsideheader =<h3><CHAT></h3>
cinsidefooter =<VER>
cdisclaimer   =<CHAT> is not responsible for any contents on external web pages. Visit at your own risk!
centrymessage =Welcome <NICK> to <CHAT>
clogoutmessage=Bye <NICK>, visit again soon!
ckickederror  =<NICK>, you have been kicked out of <CHAT>!
croomentry    =<NICK> enters <CHAT>!
croomexit     =<NICK> leaves <CHAT>.
cregmessage   =<RECP> is now a registered member of <CHAT>.
ckickedmessage=<RECP> has been kicked out of <CHAT>!
croomclean    =<CHAT> was cleaned.
cmesall       =<NICK> &#62;&nbsp;
cmesmem       =<NICK> &#62;&#62;&nbsp;
cmespm        =<font color="white">[PM to <RECP>]</font> <NICK> &#62;&#62;&nbsp;
cmesstaff     =<font color="white">[Staff]</font> <NICK> &#62;&#62;&nbsp;
ctextfilters  =1"fuck"1"***BEEEP!!!***"1"1"-GST-REG-MOD-ADM-
# controls frame
butreloadp=Reload Post Box
butreloadm=Reload Messages
butpause  =Pause
butprofile=Change Profile
butadmin  =Admin
butrules  =Rules &#38; Help
butexit   =Exit Chat
butpauseinfo=Automatic message refreshing is paused. Click <RELOAD> to resume it!
stop_action=--controls-view-redirect-captcha-
# post box frame
butsendto    =talk to
seltoall     =all chatters
seltomem     =members only
seltoadm     =staff only
butdellast   =delete last message
butdelall    =delete all messages
butdelcancel =cancel
delallconfirm=Do you really want to delete all your messages?
butmultiline =switch to multi line
butsingleline=switch to single line
kickfilter   =<NICK> has triggered an autokick filter!
# rules and help page
rules     =Rules
help      =Help
helpguests=All functions should be pretty much self-explaining, just use the buttons. In your profile you can adjust the refresh rate, font colour and your preferred input box size. You can also change your password anytime. Remember it, as you will need it for your next login!<br>Note: This is a chat, so if you don't keep talking, you will be automatically logged out after a while.
helpregs  =Members: You have some more options in your profile. You can adjust your font face, specify the frame sizes and adjust how long the entry page will be shown. You can also specify if all your private conversations should be automatically deleted as soon as you leave.
helpmods  =Moderators: Notice the Admin-button at the bottom. It'll bring up a page where you can clean messages, kick or logout chatters, view all active sessions and set guest access options.
helpadmins=Admins: You are furthermore able to register guests, edit members and register new nicks without them needing to be present in the room.
# various occasions
backtochat =Back to the chat.
savechanges=save changes
stop_action=-post-delete-help-
# waiting room / entry page
waitroom   =Waiting Room
waitmessage=Welcome <NICK>, please be patient until a moderator or admin will let you into the chat room.
reloadhelp =If this page does not reload in <REFRESH> seconds, you'll have to enable automatic redirection (meta refresh) in your browser. Also make sure no web filter, local proxy tool or browser plugin is preventing automatic refreshing! This could be for example "Polipo", "NoScript", "TorButton", "Proxomitron", etc. just to name a few.<br>As a workaround (or in case of server/proxy reload errors) you can always use the appropriate buttons at the bottom of the chat to refresh manually.
butreloadw =Reload Page
# error messages
errbadnick  =invalid nickname (<MAX> characters maximum, no special characters allowed)
errnonick   =no nickname given
errexistnick=nick exists already
erraccdenied=access denied
errbadpass  =invalid password (at least <MIN> characters required)
errbadlogin =wrong password or similar nickname in use already
frames=This chat uses <b>frames</b>. For a better chat-experience you should enable frames in your browser or use one that is able to display frames correctly and then log in again. However, you can always use the buttons at the top and bottom to switch between frames manually and everything should be functional.
stop_action=-wait-login-logout-splash-chat-
# profile page
profileheader=Your Profile
refreshrate  =Refresh rate (<MIN>-<MAX> seconds)
fontcolour   =Font colour
viewcolours  =view examples
fontface     =Font face
fontdefault  =Room Default
fontbold     =bold
fontitalic   =italic
fontexample  =example for your chosen font
boxsizes     =Post box size
boxwidth     =width:
boxheight    =height:
framesizes   =Frame sizes
frametop     =top:
framebottom  =bottom:
entryrefresh =Entry page delay (1-<DEFAULT> seconds)
exitoptions  =On exit
exitdelpms   =delete your private messages
changepass   =Change password
oldpass      =old password:
newpass      =new password:
confirmpass  =confirm new password:
succchanged  =Your profile was successfully saved.
errdiffpass  =Password confirmation does not match.
errwrongpass =Password is wrong.
# colourtable
colheader    =Colourtable
backtoprofile=Back to your profile.
stop_action=-profile-colours-
# admin waiting room/sessions
admwaiting  =Guests in Waiting Room
admsessions =Active Sessions
nicklist    =Nickname
timeoutin   =Timeout&nbsp;in
ip          =IP-Number
useragent   =Browser-Identification
allowchecked=allow checked
allowall    =allow all
denychecked =deny checked
denyall     =deny all
denymessage =Send message to denied:
butallowdeny=allow/deny
waitempty   =No more entry requests to approve.
# admin page
admheader     =Administrative Functions
admclean      =Clean Messages
admcleanall   =whole room
admcleansome  =selection
butdelsome    =delete selected messages
admkick       =Kick Chatter (<KICK> minutes)
admkickmes    =Send hint:
admkickpurge  =also purge messages
adminactive   =Logout Inactive Chatter
admvsessions  =View Active Sessions
admguests     =Guest Access
admguestsfbd  =always forbid
admguestsall  =always allow
admguestsstp  =allow while a staff member is present
admguestsapp  =require staff approval once for entry
admregguest   =Register Guest
admmembers    =Members
admregnew     =Register New Member
selmemdelete  =delete from file
selmemdeny    =deny access
selmemreg     =set to regular
selmemmod     =set to moderator
selmemadmin   =set to admin
selchoose     =(choose)
symdenied     =(!)
symguest      =(G)
symmod        =(M)
symadmin      =(A)
butadmclean   =clean
butadmkick    =kick
butadminactive=logout
butadmview    =view
butadmset     =set
butadmreg     =register
butadmstatus  =change
butadmregnew  =register
# admin messages
succreg      ="<RECP>" successfully registered.
succstatus   =Status of "<RECP>" successfully changed.
succdelmem   ="<RECP>" successfully deleted from file.
errcantreg   =cannot register "<RECP>"
errcantregnew=cannot register new member "<RECP>"
errcantkick  =cannot kick "<RECP>"
errcantlogout=cannot logout "<RECP>"
erralreadyreg="<RECP>" is already registered.
errcantstatus=cannot change status of "<RECP>"
stop_action=-admin-
# setup login
aloginname=name:
aloginpass=pass:
aloginbut =login
# descriptions on setup page
chatsetup    =Chat Setup
chataccess   =Chat Access
suspend      =suspended
enabled      =enabled
staffonly    =staff only
derefonly    =link redirection only
butset       =set
backups      =Backups
backmem      =backup members
backcfg      =backup configuration
restore      =restore backup
backdat      =Backup data to copy/paste.
directories  =Server Directories
dirsinfo     =If you want to share existing members and temporary guests of another chat on this server, you can specify the data directory of that chat here. This setting affects Backups (members) and Main Admins below. Any directories set here must exist on the server already. Changing these values will suspend this chat and delete all current chat sessions and messages, so only set them once initially!
membersdir   =Data directory of member and guest files to be used (defaults to "<DEFAULT>" if empty)
captchalibdir=Directory where optional CAPTCHA modules are stored ("LeCaptcha*.pm")
captchaimgdir=Web directory for temporary image-files from CAPTCHAs to show (relative path, must be readable by the web-user)
savedirs     =save directory settings
mainadmins   =Main Admins
regadmin     =Register new Main Admin
raiseadmin   =Raise to Main Admin
loweradmin   =Lower to Regular Admin
butregadmin  =register
butraise     =raise
butlower     =lower
cfglanguage  =Language Settings
editlanguage =create/edit language files
resetlanguage=reset language to the default (english)
cfgsettings  =Change Configuration Settings
cfgmainadm   =Log in with your main admin nick instead of the superuser to change particular chat settings!
butlogout    =log out
lastchanged  =Last changed:
# sections for export/import
secgeneral=General Options
secfilters=Content Filters
seccustom =Custom HTML
secrules  =Rules and Help
secnotify =Messages and Notifications
secstyles =Colours and Styles
# browser
title        =Browser title / name of your chat
favicon      =Browser icon URL (favicon)
# redirection
redirifsusp  =Redirect to alternate URL if suspended
redirtourl   =Redirection URL
# options
yes           =yes
no            =no
allowfonts    =Allow change of font face
allowmultiline=Allow multiline messages
allowpms      =Allow private messages
rndguestcol   =Randomise default colour for guests
autocleanup   =Remove all messages when room is empty
keepguests    =Keep existing guests in room if entry is closed
# auto hotlinks
createlinks   =Create hotlinks from URLs
maxlinklength =Maximum characters for hotlinks to display
showdisclaimer=Show disclaimer on redirection page
useextderef   =Use external link redirection script
extderefurl   =External link redirection script URL
# at nicknames
createatnicks =Style nicknames posted as @nickname
atnicksym     =Symbol for styled @nicknames
# splash screen
splashshow    =Show splash screen before login
splashall     =Splash screen also for members
captchause    =Use CAPTCHA on splash screen
captchaall    =CAPTCHA also for members
captchamodule =CAPTCHA module to use
# values
sessionexpire  =Minutes of silence until member session expires
guestsexpire   =Minutes of silence until guest session expires
messageexpire  =Minutes until messages get removed
kickpenalty    =Minutes nickname is blocked after beeing kicked
captchaexpire  =Minutes until CAPTCHAs expire
waitingexpire  =Minutes until guest entry requests expire
guestspreserve =Hours to remember guest logins (at least session+message expiration is always used)
hideguests     =Number of guests from which on to shorten list and hide entry/exit
defaultrefresh =Default refresh time (seconds)
minrefresh     =Minimum refresh time (seconds)
maxrefresh     =Maximum refresh time (seconds)
floodlimit     =Minimum time between posts from same nick (seconds)
boxwidthdef    =Default post box width
boxheightdef   =Default post box height
maxmessage     =Maximum message length
maxname        =Maximum characters for nickname
minpass        =Minimum characters for password
# text filters
filterslist    =Available filters
filtersnew     =Add new filter
fpriority      =Priority:
factive        =Filter is active.
fdisabled      =Filter is disabled.
fdelete        =Delete this filter!
fvalid         =Filter is valid for:
fvalidGST      =Guests
fvalidREG      =Registered members
fvalidMOD      =Moderators
fvalidADM      =Admins
fregexerror    =Regular expression contains errors!
fchoosetype    =(choose filter type)
ftypetext      =Find exact words (separated by "|"):
ftyperegex     =Match regular expression:
fchooseaction  =(choose filter action)
factionreplace =Replace matched text with:
factionkick    =Kick chatter, replace text with:
factionpurge   =Kick, purge and send message:
factionsendpm  =Send private message to chatter:
factionsysmes  =Post as system notification if public:
fseparator     =------------------------------------------------------------
# place holder info
placeholders   =Filter replacements and the HTML fields below accept the following place holders where applicable:
CHAT           =name of the chat
RULES          =rules text
HELP           =help text
ADDHELP        =additional help text
IP             =users IP-address
VER            =version of this script
TIME           =current time (GMT-offset: &#60;TIME-0600&#62;)
DATE           =current date (GMT-offset: &#60;DATE+0930&#62;)
NICK           =sender of message or admin action
RECP           =recipient of message or admin action
ALL            =list of all chatters in room
ALLNUM         =number of all chatters in room
GUESTS         =list of all guests in room
GUESTSNUM      =number of all guests in room
MEMBERS        =list of all members in room
MEMBERSNUM     =number of all members in room
STAFF          =list of all staff in room
STAFFNUM       =number of all staff in room
whitespaceinfo =Note: Leading and trailing whitespace in the HTML fields will be removed. Use '&#38;nbsp;' for a space at the beginning or the end!
gmtoffset      =Default GMT-offset for &#60;DATE&#62; and &#60;TIME&#62;, e.g. +0100
# text
header         =Login page header
noguests       =Text if no guests allowed
nomembers      =Text if staff only allowed
loginbutton    =Login button text
footer         =Login page footer
splashtxt      =Splash screen
splashcnt      =Continue button text
insideheader   =Header inside chatroom
insidefooter   =Footer inside chatroom
frametopdef    =Top frame default height
framebottomdef =Bottom frame default height
disclaimer     =Disclaimer header for external link redirections
rulestxt       =Rules
addhelpgst     =Additional help text for guests (e.g. registration requirements)
addhelpreg     =Additional help text for registered members (e.g. to explain smiley filters)
addhelpmod     =Additional help text for moderators (e.g. moderation guidelines)
addhelpadm     =Additional help text for administrators (e.g. admin filters or staff-room URL)
entrymessage   =Entry page message
logoutmessage  =Logout page message
kickederror    =Kicked error page message
# system notifications
roomentry      =Entry notification
roomexit       =Exit notification
regmessage     =Register notification
kickedmessage  =Kick notification
roomclean      =Cleaning notification
sysbefore      =Text before system notifications
sysafter       =Text after system notifications
# user messages
mesall         =Message to all
mesmem         =Message to members
messtaff       =Staff Messages
mespm          =Private Messages
mesbefore      =Text before messages
mesafter       =Text after messages
sysnick        =Nickname for messages from the system
# default colours for body and non-CSS browsers
colbg          =Background colour
coltxt         =Text colour
collnk         =Link colour
colvis         =Visited link colour
colact         =Active link colour
# styles
cssglobal      =CSS for all pages
styleback      =Back button style
csslogin       =CSS login page
stylelogintext =Textfield style
stylecolselect =Selection style
styleenter     =Login button style
csssplash      =CSS splash page
stylesplashcnt =Continue button style
csspost        =CSS post frame
styleposttext  =Post text style
stylepostsend  =Talk to button style
stylesendlist  =Send list style
styledellast   =Delete last button style
styledelall    =Delete all button style
styleswitch    =Multiline button style
cssview        =CSS messages frame
styletoplist   =Chatters list style
styledelsome   =Delete selected button style
stylecheckwait =Check newcomers button style
csswait        =CSS waiting room
stylewaitrel   =Reload button style
csscontrols    =CSS controls frame
stylerelpost   =Reload post box button style
stylerelmes    =Reload messages button style
stylepause     =Pause button style
styleprofile   =Profile button style
styleadmin     =Admin button style
stylerules     =Rules button style
styleexit      =Exit button style
cssprofile     =CSS profile page
cssrules       =CSS rules page
cssnote        =CSS notification pages
cssadmin       =CSS admin pages
csssetup       =CSS setup pages
csserror       =CSS error pages
# initialisation stuff
invalidbackup =No valid backup data given.
membrestfail  =Restoring members failed:
membrestsucc  =Restoring members succeeded.
membrestinval =Invalid data for members file.
confrestfail  =Restoring configuration failed:
confrestsucc  =Restoring configuration succeeded.
confrestinval =Invalid data for configuration file.
langrestfail  =Restoring language failed:
langrestsucc  =Restoring language succeeded.
langrestinval =Invalid data for language file.
raisemainsucc ="<RECP>" raised to main admin.
raisemaindone ="<RECP>" is already main admin.
raisemainfail ="<RECP>" is not an admin.
lowerregsucc  ="<RECP>" lowered to regular admin.
lowerregdone  ="<RECP>" is already regular admin.
lowerregfail  ="<RECP>" is not an admin.
newmainreg    =New main admin "<RECP>" registered.
errbaddata    =Invalid data received.
initsetup     =Initial Setup
setsu         =Superuser Login
setsunick     =Superuser nickname:
setsupass     =Superuser password:
setsupassconf =Confirm password:
setsuhelp     =In case of file corruption on the server, you can still restore backups with your superuser nick. You will also need it to install main admins who will be able to make changes to the chat setup, suspend/unsuspend the chat and upgrade members to moderators and regular admins.<br>You can not alter your superuser login later, so choose a secret nick and a very strong pass here. Take a nick that will not show up in the chat room. If you ever need to reset the superuser, you will have to delete the file "<DATA>/admin" on the server and do this setup here again.
initback      =Restore Backups
initbackhelp  =If you want to recover files (members, config, language) from existing backup data, paste it all here:
initbut       =initialise chat
suerrfileexist=A superuser file exists already!
suerrbadnick  =Invalid nickname for superuser (<MAX> characters maximum, no special characters allowed). Try again!
suerrbadpass  =Password is too short, <MIN> characters required. Try again!
suerrbadpassc =Password confirmation does not match. Try again!
suwritesucc   =Superuser file was written successfully.<br><br><p align="left">Important: Please make sure the data directory and files are not accessible from the web, or an attacker could read all messages and take over sessions from chatters! The script did attempt to set the correct chmod settings, but depending on your server configuration you might still be vulnerable. If you do <em>not</em> get an error message when accessing <a href="<DATA>">this directory</a> or <a href="<DATA>/admin">this file</a>, then you must protect the data directory directly in your server configuration (e.g. with a .htaccess file) or edit the script at the beginning and change the data directory to a path outside of your web-directory. At least give it a random, unguessable name if all else fails and then do this setup here again!</p>
suwritefail   =Superuser file was not written correctly. Please try again!<br><br><p align="left">If this error persists, make sure the script is allowed to create files and folders. Possibly you may have to create the data folder "<DATA>" manually first.</p>
initgotosetup =Go to the Setup-Page.
initlechattxt =Results of lechat.txt:
# language editing
lngheader  =Language File Editor
lnghelp    =Fill in your translations below the original texts and save your changes. Use the corresponding HTML entities to display special characters! (&nbsp;'&#38;'&nbsp;=&nbsp;'&#38;#38;'&nbsp;, '&#60;'&nbsp;=&nbsp;'&#38;#60;'&nbsp;, '&#62;'&nbsp;=&nbsp;'&#38;#62;'&nbsp;)<br>To apply your edits to the chat, create a backup here and restore that on the setup page. For empty entries, the english defaults will be used.
lngload    =restore language editing data from backup
lngbackup  =create backup from saved editing data
lngtoken   =Token
lngdeftxt  =Default Text
backtosetup=Back to the Setup-Page.

-----BEGIN PGP SIGNATURE-----

iQA/AwUBWk/3g8r7q1ZyCqQiEQI6KgCg6N+MU/okEQPxZH9baHlCGb9E+2oAnR3n
j6gB8XqiunXmgRAKypNCMcbG
=f54l
-----END PGP SIGNATURE-----
