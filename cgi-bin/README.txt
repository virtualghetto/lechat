
TL:DR Setup perl cgi. Paste Zip content's excluding txt files into web directory.
TL:DR Visit http://(server)/(cgi-path)/(script-name).cgi?action=setup and follow the instructions.

Non-lazy way (provides more information):

Note: This is a modified version from "Friendly Script Updater".
#####################################################################
#                                                                   #
#    #      #####        ####  #   #   ###   #####      /\_/\       #
#    #      #           #      #   #  #   #    #       ( o.o )      #
#    #      ###         #      #####  #####    #        > ^ <       #
#    #      #           #      #   #  #   #    #        v1.20       #
#    #####  #####        ####  #   #  #   #    #       2015-07      #
#                                                                   #
#  Installation instructions:                                       #
#                                                                   #
#  Upload this file into your cgi-bin directory (you can rename it  #
#  to whatever  you want,  if you prefer)  and make it  executable  #
#  (chmod 711).  If you have language data or backups  you want to  #
#  restore initially,  you can copy that all into a textfile named  #
#  "lechat.txt" and put it next to your script file on the server.  #
#  Then call the script in your browser with parameter like this:   #
#                                                                   #
#  http://(server)/(cgi-path)/(script-name).cgi?action=setup        #
#                                                                   #
#  All necessary installation settings can be made from there.      #
#  The server needs to support Perl CGI scripts, obviously. If you  #
#  have trouble,  make sure the file is uploaded in ASCII-mode and  #
#  Perl scripts are allowed to create files and folders.            #
#  Banner killers for some known hosts are built in, please report  #
#  back any problems there or any other hosts you want added!       #
#                                                                   #
#  If you make translations and want to share them, please send me  #
#  a copy of the backup data for my website, thanks!  All text can  #
#  be edited conveniently as superuser on the setup page.           #
#                                                                   #
#  This script comes  without any  warranties.  Use it at your own  #
#  risk, don't  blame me for any modifications you make. Verify my  #
#  attached  PGP-signature, to make sure  you got the original and  #
#  not an altered copy! Really, do verify it!                       #
#  If you spread the script,  please only give  away the original,  #
#  or better, just refer to: http://4fvfamdpoulu2nms.onion/lechat/  #
#                                                                   #
#  If you add your own cool features and want to share with others, #
#  feel free,  but please  modify at least the version tag and add  #
#  your name to it, so it is clear that it is not my original code  #
#  anymore.  If you send  me a copy of your edited script, I might  #
#  use some of your ideas in future versions. Thank you!            #
#                                                                   #
#  I wrote the script from scratch and all the code is my own, but  #
#  as you may notice,  I took some ideas  from other scripts  that  #
#  are out there. Bug reports and feedback are very welcome.        #
#                                                                   #
#  The "LE" in the name  you can take as  "Lucky Eddie", or  since  #
#  the script was  meant to be lean  and easy on server resources,  #
#  as "Light Edition". It may even be the french word for "the" if  #
#  you prefer. Translated from french to english, "le chat" means:  #
#  "the cat".                                                       #
#                                                                   #
#  Other than that, enjoy! ;)                                       #
#                                                                   #
#  Lucky Eddie                                                      #
#                                                                   #
#  Edit: This is a revision of the script added features are:       #
#  -Added in-line moderation:                                       #
#      -"/kick [message]:[user]" //Kick [user] with the [message]   #
#      -"/delmess [user]" //Deletes all users messages              #
#      -"/clean room" //Clears the rooms messages                   #
#      -"/logout [user]" //Logs out [user]                          #
#      -"/name [user]" // Adds user to banned name list.            #
#                                                                   #
#  - Fixed some html errors to make the script a tad bit faster     #
#  - Centered everything for continuity.                            #
#  - When the user presses delete all it will ask for comfirmation  #
#  - Added Links                                                    #
#      -The /[command] only works when the user is admin or mod     #
#                                                                   #
#  - Added Link Shortener                                           #
#  - Updated Rules & Help                                           #
#      -Included in-line moderation changes explaination            #
#      -Added list of included emojis                               #
#                                                                   #
#  - Name fliter intergration to block unwanted names               #
#      -When using the /name command it adds the name to a list     #
#      -Before someone gains access to the chat it checks the name  #
#      -Full number names are also blocked.                         #
#                                                                   #
#####################################################################