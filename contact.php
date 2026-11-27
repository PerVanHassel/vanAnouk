<?php
/**
 * vanAnouk — contactformulier
 *
 * Vervangt het WordPress-formulier (Contact Form 7). Werkt op elke hosting met
 * PHP (zoals bhosted). Op GitHub Pages draait geen PHP; daar kan het formulier
 * dus niet echt versturen.
 *
 * Antwoord in hetzelfde formaat als Contact Form 7, zodat de site precies
 * dezelfde meldingen toont.
 */

$RECIPIENT = 'info@vananouk.nl';
$SENDER    = 'vanAnouk <info@vananouk.nl>';
$SITE_URL  = 'http://vananouk.nl';

$wantsJson = isset($_SERVER['HTTP_ACCEPT']) && strpos($_SERVER['HTTP_ACCEPT'], 'application/json') !== false;

function respond($data, $wantsJson)
{
	if ($wantsJson) {
		header('Content-Type: application/json; charset=utf-8');
		echo json_encode($data);
	} else {
		// zonder JavaScript: terug naar de contactpagina
		$status = isset($data['status']) ? $data['status'] : 'mail_failed';
		header('Location: contact/?status=' . urlencode($status) . '#wpcf7-f45-p46-o1', true, 303);
	}
	exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
	header('Location: contact/', true, 302);
	exit;
}

$field = function ($name) {
	return isset($_POST[$name]) ? trim((string) $_POST[$name]) : '';
};

// eenvoudige spambeveiliging: verborgen veld moet leeg zijn, controleveld gevuld
if ($field('_va_website') !== '' || strpos($field('_va_check'), 'ok-') !== 0) {
	respond(array('status' => 'spam'), $wantsJson);
}

$name    = str_replace(array("\r", "\n"), ' ', $field('your-name'));
$email   = str_replace(array("\r", "\n"), '', $field('email'));
$message = $field('your-message');

$invalid = array();
if ($name === '') {
	$invalid[] = array('into' => 'your-name', 'message' => 'Het veld is verplicht.');
}
if ($email === '') {
	$invalid[] = array('into' => 'email', 'message' => 'Het veld is verplicht.');
} elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
	$invalid[] = array('into' => 'email', 'message' => 'The e-mail address entered is invalid.');
}
if ($invalid) {
	respond(array('status' => 'validation_failed', 'invalidFields' => $invalid), $wantsJson);
}

$subject = 'vanAnouk "Contactformulier"';
$body = "Van: {$name} <{$email}>\n"
	. "Onderwerp: Contactformulier\n\n"
	. "Berichtinhoud:\n{$message}\n\n"
	. "-- \n"
	. "Deze e-mail is verzonden vanuit het contactformulier op vanAnouk {$SITE_URL}";

$headers = 'From: ' . $SENDER . "\r\n"
	. 'Reply-To: ' . $email . "\r\n"
	. "MIME-Version: 1.0\r\n"
	. "Content-Type: text/plain; charset=UTF-8\r\n"
	. "Content-Transfer-Encoding: 8bit\r\n";

$encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
$sent = @mail($RECIPIENT, $encodedSubject, $body, $headers);

respond(array('status' => $sent ? 'mail_sent' : 'mail_failed'), $wantsJson);
