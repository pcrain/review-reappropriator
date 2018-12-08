<?php

// curl -X POST -d '{"feedback":"ram"}' -H 'Content-Type: application/json' "127.0.0.1:8888/miniserver.php"
// curl -X POST -d @./request.json -H 'Content-Type: application/json' "127.0.0.1:8888/miniserver.php"

  $PYSERVADDR = "127.0.0.1";
  $PYSERVPORT = 50507;

  //Send arbitrary bytes through a socket
  function sendBytes($g,$length,$socket) {
    $totalsent = 0;
    while ($totalsent < $length) {
      $newsent = socket_write($socket, implode(array_map("chr", $g)), $length-$totalsent);
      if ($newsent == 0) {
        throw new Exception('Connection broken.');
      }
      $totalsent += $newsent;
    }
  }

  //Send an arbitrary integer through a socket
  function sendInt($i,$socket) {
    if ($i <= 256/2) { //TODO: does not work for 128-256
      $b = unpack("C*", pack("C", $i));
      $nbytes = 1;
    }
    else if ($i <= 65536/2) {
      $b = unpack("C*", pack("n", $i));
      $nbytes = 2;
    }
    else {
      throw new Exception('Unsupported int size.');
    }
    sendBytes(unpack("C*", pack("c", $nbytes)),1,$socket);
    sendBytes($b,$nbytes,$socket);
  }

  //Send an arbitrary string through a socket
  function sendString($s,$socket) {
    $m = unpack('C*', $s);
    $mlen = sizeof($m);
    consoleP($mlen);
    sendInt($mlen,$socket);
    sendBytes($m,$mlen,$socket);
  }

  //Receive arbitrary bytes through a socket
  function receiveBytes($length, $socket) {
    $out = '';
    $ret = '';
    $bytes_recd = 0;
    while ($bytes_recd < $length) {
      $newrecv = socket_recv($socket, $out, $length-$bytes_recd, 0);
      if ($newrecv == 0) {
        throw new Exception('Connection broken.');
      }
      $ret .= $out;
      $bytes_recd += $newrecv;
    }
    return $ret;
  }

  //Receive an arbitrary integer through a socket
  function receiveInt($socket) {
    $nbytes = ord(receiveBytes(1,$socket));                      // Determine the size of the message size
    $out = receiveBytes($nbytes,$socket);                        // Receive int of size $nbytes
    $c = unpack("C*",$out);                                      // Unpack the array
    $pad = array_pad($c,-4,0);                                   // Pad it to four bytes
    $i = unpack("N",pack("C*",$pad[0],$pad[1],$pad[2],$pad[3])); // Repack it as a 4 byte int
    return $i[1];                                                // Return the first element of the resulting array
  }

  //Receive an arbitrary string through a socket
  function receiveString($socket) {
    $mlen = receiveInt($socket);
    $s = receiveBytes($mlen,$socket);
    return $s;
  }

  //Decode hex string
  //per Elvin Risti @ https://stackoverflow.com/questions/13774215/convert-hex-code-into-readable-string-in-php
  function decode_code($code) {
    return preg_replace_callback('@\\\(x)?([0-9a-f]{2,3})@',
      function ($m) {
        if ($m[1]) {
          $hex = substr($m[2], 0, 2);
          $unhex = chr(hexdec($hex));
          if (strlen($m[2]) > 2) {
            $unhex .= substr($m[2], 2);
          }
          return $unhex;
        } else {
          return chr(octdec($m[2]));
        }
      }, $code);
  }

  //Decode JSON string with \xx values
  function stripEncodedString($s) {
    $r = decode_code($s);                   //Remove \x?? strings
    $r = stripslashes($r);                  //Strip JSON slashes
    $r = preg_replace("/\"\"/", "\"", $r);  //Remove double-double quotes
    $r = preg_replace("/^\"|\"$/", "", $r); //Remove quotes at the ends of the string
    return $r;
  }

  //Set up a socket
  function connectToPythonFeedbackServer() {
    global $PYSERVADDR, $PYSERVPORT;

    // Allow the script to hang around waiting for connections.
    set_time_limit(0);

    // Turn on implicit output flushing so we see what we're getting as it comes in.
    ob_implicit_flush();

    // Create a TCP/IP socket.
    $s = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
    if ($s === false) {
      echo "socket_create() failed: reason: " . socket_strerror(socket_last_error()) . "\n";
    }

    // Attempt to connect
    $result = socket_connect($s, $PYSERVADDR, $PYSERVPORT);
    if ($result === false) {
      echo "socket_connect() failed.\nReason: ($result) " . socket_strerror(socket_last_error($s)) . "\n";
    }

    // 3 second recv timeout
    // socket_set_option($s, SOL_SOCKET, SO_RCVTIMEO, array('sec' => 3, 'usec' => 0));

    // 3 second send timeout
    // socket_set_option($s, SOL_SOCKET, SO_SNDTIMEO, array('sec' => 3, 'usec' => 0));

    // Allow the socket to block
    socket_set_block($s);

    // Return the socket for further use
    return $s;
  }

  function genQueryFromPost() {
    // consoleP(var_dump($_POST));
    // return "ram";
    // echo var_dump(getallheaders());
    $raw_input = file_get_contents('php://input');
    consoleP($raw_input);
    $_post = json_decode($raw_input,true);
    consoleP($_post['feedback']);
    return $_post['feedback'];
  }

  //Print to PHP console stderr
  function consoleP($text,$end="\n") {
    file_put_contents('php://stderr', print_r("\033[1;36m" . $text . "\033[0m", TRUE));
    file_put_contents('php://stderr', print_r($end, TRUE));
  }

  //Print to PHP console stderr
  function dbugP($text,$end="\n") {
    file_put_contents('php://stderr', print_r("\033[1;35m" . $text . "\033[0m", TRUE));
    file_put_contents('php://stderr', print_r($end, TRUE));
  }

  //Use a socket
  $command = genQueryFromPost();        // Prepare the data
  $s = connectToPythonFeedbackServer(); // Attempt to connect to python fb server
  sendString($command,$s);              // Send the requisite data
  $r = receiveString($s);               // Get the response
  socket_close($s);                     // Close the socket
  consoleP($r);
  header('Content-Type: application/json');
  header('Response-Type: application/json');
  header("Access-Control-Allow-Origin: *");
  header('Accept: application/json');
  echo json_encode($r);           // Print the response

?>
