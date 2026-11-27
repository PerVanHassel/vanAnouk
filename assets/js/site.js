/*!
 * vanAnouk — site behaviour (no dependencies)
 * Rebuilds the interactions of the original WordPress site:
 * mobile menu, cookie notice, image lightbox, home intro animation
 * and the contact form.
 */
(function () {
	'use strict';

	var doc = document;
	var win = window;

	/* ------------------------------------------------------------------ */
	/* Helpers                                                              */
	/* ------------------------------------------------------------------ */

	function $(sel, ctx) { return (ctx || doc).querySelector(sel); }
	function $$(sel, ctx) { return Array.prototype.slice.call((ctx || doc).querySelectorAll(sel)); }

	// jQuery "swing" easing, which the original used for its animations.
	function swing(p) { return 0.5 - Math.cos(p * Math.PI) / 2; }

	// Animate numeric style properties (px or opacity) like jQuery.animate.
	function animate(el, props, duration, done) {
		var start = {};
		var keys = Object.keys(props);
		var cs = win.getComputedStyle(el);
		keys.forEach(function (k) { start[k] = parseFloat(el.style[k] !== '' ? el.style[k] : cs[k]) || 0; });
		if (el._anim) { win.cancelAnimationFrame(el._anim); }
		var t0 = null;
		function step(ts) {
			if (t0 === null) { t0 = ts; }
			var p = Math.min(1, (ts - t0) / duration);
			var e = swing(p);
			keys.forEach(function (k) {
				var v = start[k] + (props[k] - start[k]) * e;
				el.style[k] = (k === 'opacity') ? String(v) : v + 'px';
			});
			if (p < 1) { el._anim = win.requestAnimationFrame(step); }
			else { el._anim = null; if (done) { done(); } }
		}
		el._anim = win.requestAnimationFrame(step);
	}

	function fadeIn(el, duration, done) {
		el.style.display = el.dataset.display || 'block';
		el.style.opacity = el.style.opacity === '' ? '0' : el.style.opacity;
		animate(el, { opacity: 1 }, duration, done);
	}

	function fadeOut(el, duration, done) {
		animate(el, { opacity: 0 }, duration, function () {
			el.style.display = 'none';
			if (done) { done(); }
		});
	}

	// jQuery-style slideDown / slideUp (height animation).
	function slideDown(el, duration) {
		el.style.display = 'block';
		el.style.overflow = 'hidden';
		var h = el.scrollHeight;
		el.style.height = '0px';
		animate(el, { height: h }, duration, function () {
			el.style.height = '';
			el.style.overflow = '';
		});
	}

	function slideUp(el, duration) {
		el.style.overflow = 'hidden';
		el.style.height = el.offsetHeight + 'px';
		animate(el, { height: 0 }, duration, function () {
			el.style.display = 'none';
			el.style.height = '';
			el.style.overflow = '';
		});
	}

	function isVisible(el) { return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length); }

	/* ------------------------------------------------------------------ */
	/* Mobile menu                                                         */
	/* ------------------------------------------------------------------ */

	function initMobileMenu() {
		var toggle = $('.menu-toggle span');
		var list = $('.mobile-nav > ul');
		if (!toggle || !list) { return; }
		toggle.addEventListener('click', function (e) {
			e.preventDefault();
			if (isVisible(list)) { slideUp(list, 200); } else { slideDown(list, 200); }
		});
		$$('.mobile-nav a, .logo').forEach(function (a) {
			a.addEventListener('click', function () {
				if (isVisible(list)) { slideUp(list, 400); }
			});
		});
	}

	/* ------------------------------------------------------------------ */
	/* Cookie notice (same behaviour as the "Cookie Notice" plugin)        */
	/* ------------------------------------------------------------------ */

	var COOKIE_NAME = 'cookie_notice_accepted';
	var COOKIE_TIME = 604800; // 7 days, as configured on the original site
	var SCROLL_OFFSET = 100;  // accepting by scrolling more than 100px

	function getCookieNotice() {
		var parts = ('; ' + doc.cookie).split('; ' + COOKIE_NAME + '=');
		return parts.length === 2 ? parts.pop().split(';').shift() : undefined;
	}

	function initCookieNotice() {
		var notice = $('#cookie-notice');
		if (!notice) { return; }

		function onScroll() {
			if ((win.pageYOffset || doc.documentElement.scrollTop) > SCROLL_OFFSET) { setCookie('accept'); }
		}

		function setCookie(value) {
			win.removeEventListener('scroll', onScroll);
			var expires = new Date(Date.now() + COOKIE_TIME * 1000);
			var val = value === 'accept' ? 'true' : 'false';
			doc.cookie = COOKIE_NAME + '=' + val + ';expires=' + expires.toUTCString() + ';path=/;' + (location.protocol === 'https:' ? 'secure;' : '');
			doc.body.classList.remove('cookies-not-set');
			doc.body.classList.add('cookies-set', val === 'true' ? 'cookies-accepted' : 'cookies-refused');
			fadeOut(notice, 400);
		}

		$$('.cn-set-cookie', notice).forEach(function (btn) {
			btn.addEventListener('click', function (e) {
				e.preventDefault();
				setCookie(btn.getAttribute('data-cookie-set'));
			});
		});

		var current = getCookieNotice();
		if (current === undefined) {
			win.addEventListener('scroll', onScroll);
			notice.style.visibility = 'visible';
			notice.style.display = 'none';
			doc.body.classList.add('cookies-not-set');
			fadeIn(notice, 400);
		} else {
			doc.body.classList.add('cookies-set', current === 'true' ? 'cookies-accepted' : 'cookies-refused');
		}
	}

	/* ------------------------------------------------------------------ */
	/* Lightbox (replica of the prettyPhoto lightbox used on the original) */
	/* ------------------------------------------------------------------ */

	var LB_SPEED = 400;          // jQuery "normal"
	var LB_PADDING = 16;         // horizontal padding of the pp_default theme
	var LB_DETAILS_HEIGHT = 44;  // height reserved below the image (nav + margins)

	function initLightbox() {
		var links = $$('a[data-lightbox]');
		if (!links.length) { return; }

		var items = links.map(function (a) { return { href: a.getAttribute('href'), title: a.getAttribute('title') || '' }; });
		var overlay, holder, titleEl, content, fade, imgWrap, img, counter, loader;
		var index = 0, opened = false, busy = false;

		function build() {
			overlay = doc.createElement('div');
			overlay.className = 'lb-overlay';
			holder = doc.createElement('div');
			holder.className = 'lb-holder';
			holder.innerHTML =
				'<div class="lb-title">&nbsp;</div>' +
				'<div class="lb-content">' +
					'<div class="lb-loader"></div>' +
					'<div class="lb-fade">' +
						'<div class="lb-hover"></div>' +
						'<div class="lb-image-wrap"><img alt=""></div>' +
						'<div class="lb-details">' +
							'<div class="lb-nav">' +
								'<a href="#" class="lb-prev">Previous</a>' +
								'<p class="lb-counter">1/1</p>' +
								'<a href="#" class="lb-next">Next</a>' +
							'</div>' +
							'<a class="lb-close" href="#">Close</a>' +
						'</div>' +
					'</div>' +
				'</div>';
			doc.body.appendChild(overlay);
			doc.body.appendChild(holder);
			titleEl = $('.lb-title', holder);
			content = $('.lb-content', holder);
			fade = $('.lb-fade', holder);
			imgWrap = $('.lb-image-wrap', holder);
			img = $('img', holder);
			counter = $('.lb-counter', holder);
			loader = $('.lb-loader', holder);

			overlay.addEventListener('click', close);
			$('.lb-close', holder).addEventListener('click', function (e) { e.preventDefault(); close(); });
			$('.lb-prev', holder).addEventListener('click', function (e) { e.preventDefault(); change(-1); });
			$('.lb-next', holder).addEventListener('click', function (e) { e.preventDefault(); change(1); });
			doc.addEventListener('keydown', function (e) {
				if (!opened) { return; }
				if (e.keyCode === 37) { change(-1); e.preventDefault(); }
				else if (e.keyCode === 39) { change(1); e.preventDefault(); }
				else if (e.keyCode === 27) { close(); e.preventDefault(); }
			});
			win.addEventListener('resize', function () { if (opened && !busy) { layout(false); } });
		}

		// Height the original reserved for the title (it measured a clone that
		// always came out one line taller than the visible title).
		function titleHeight(width) {
			var probe = doc.createElement('div');
			probe.className = 'lb-title';
			probe.style.cssText = 'position:absolute;top:-10000px;left:0;visibility:hidden;width:' + width + 'px';
			probe.innerHTML = titleEl.innerHTML;
			doc.body.appendChild(probe);
			var h = probe.offsetHeight;
			doc.body.removeChild(probe);
			return 5 + h + 26;
		}

		function dimensions(w, h) {
			var winW = doc.documentElement.clientWidth;
			var winH = win.innerHeight;
			var imgW = w, imgH = h;
			var cw = imgW, ch = imgH + LB_DETAILS_HEIGHT + titleHeight(imgW);
			if (cw > winW || ch > winH) {
				var fitting = false;
				while (!fitting) {
					if (cw > winW) { imgW = winW - 200; imgH = h / w * imgW; }
					else if (ch > winH) { imgH = winH - 200; imgW = w / h * imgH; }
					else { fitting = true; }
					ch = imgH; cw = imgW;
				}
				ch = imgH + LB_DETAILS_HEIGHT + titleHeight(imgW);
				cw = imgW;
			}
			return {
				width: Math.floor(imgW),
				height: Math.floor(imgH),
				containerWidth: Math.floor(cw) + 2 * LB_PADDING,
				containerHeight: Math.floor(ch),
				contentWidth: Math.floor(imgW),
				contentHeight: Math.floor(imgH + LB_DETAILS_HEIGHT)
			};
		}

		function layout(animated, done) {
			var d = dimensions(img.naturalWidth || 800, img.naturalHeight || 645);
			var winW = doc.documentElement.clientWidth;
			var top = (win.pageYOffset || doc.documentElement.scrollTop) + (win.innerHeight / 2 - d.containerHeight / 2);
			if (top < 0) { top = 0; }
			var left = winW / 2 - d.containerWidth / 2;
			if (left < 0) { left = 0; }
			titleEl.style.width = d.width + 'px';
			$('.lb-details', holder).style.width = d.width + 'px';
			img.style.width = d.width + 'px';
			img.style.height = d.height + 'px';
			$('.lb-hover', holder).style.width = d.width + 'px';
			$('.lb-hover', holder).style.height = d.height + 'px';
			overlay.style.height = Math.max(doc.documentElement.scrollHeight, doc.body.scrollHeight) + 'px';
			overlay.style.width = winW + 'px';
			if (animated) {
				animate(content, { height: d.contentHeight, width: d.contentWidth }, LB_SPEED);
				animate(holder, { top: top, left: left, width: d.containerWidth }, LB_SPEED, done);
			} else {
				content.style.height = d.contentHeight + 'px';
				content.style.width = d.contentWidth + 'px';
				holder.style.top = top + 'px';
				holder.style.left = left + 'px';
				holder.style.width = d.containerWidth + 'px';
				if (done) { done(); }
			}
		}

		function show(i, first) {
			busy = true;
			index = (i + items.length) % items.length;
			var item = items[index];
			counter.textContent = (index + 1) + '/' + items.length;
			if (item.title) { titleEl.textContent = item.title; } else { titleEl.innerHTML = '&nbsp;'; }
			loader.style.display = 'block';
			var pre = new Image();
			pre.onload = function () {
				var startAnimation = function () {
					loader.style.display = 'none';
					img.src = item.href;
					animate(titleEl, { opacity: 1 }, LB_SPEED);
					layout(true, function () {
						fade.style.display = 'block';
						fade.style.opacity = '0';
						animate(fade, { opacity: 1 }, LB_SPEED, function () { busy = false; });
					});
				};
				if (first) { setTimeout(startAnimation, Math.max(0, LB_SPEED - (Date.now() - openedAt))); }
				else { startAnimation(); }
			};
			pre.src = item.href;
		}

		var openedAt = 0;
		function open(i) {
			if (!overlay) { build(); }
			opened = true;
			openedAt = Date.now();
			var winW = doc.documentElement.clientWidth;
			overlay.style.display = 'block';
			overlay.style.opacity = '0.7';
			overlay.style.height = Math.max(doc.documentElement.scrollHeight, doc.body.scrollHeight) + 'px';
			overlay.style.width = winW + 'px';
			// starts as a small box in the middle of the screen
			fade.style.display = 'none';
			titleEl.style.opacity = '0';
			holder.style.width = '100px';
			content.style.width = '100px';
			content.style.height = '40px';
			holder.style.left = (winW / 2 - 50) + 'px';
			holder.style.top = ((win.pageYOffset || doc.documentElement.scrollTop) + win.innerHeight / 2 - 20) + 'px';
			holder.style.opacity = '0';
			holder.style.display = 'block';
			animate(holder, { opacity: 1 }, LB_SPEED);
			show(i, true);
		}

		function change(dir) {
			if (busy || !opened) { return; }
			busy = true;
			animate(fade, { opacity: 0 }, LB_SPEED, function () {
				fade.style.display = 'none';
				show(index + dir, false);
			});
		}

		function close() {
			if (!opened) { return; }
			opened = false;
			animate(holder, { opacity: 0 }, LB_SPEED, function () {
				holder.style.display = 'none';
				overlay.style.display = 'none';
				busy = false;
			});
		}

		links.forEach(function (a, i) {
			a.addEventListener('click', function (e) {
				e.preventDefault();
				open(i);
			});
		});
	}

	/* ------------------------------------------------------------------ */
	/* Home intro animation (was a Slider Revolution slide)                */
	/* ------------------------------------------------------------------ */

	function initHero() {
		var hero = $('#hero');
		if (!hero) { return; }
		var bg = $('.hero-bg', hero);
		var image = $('.hero-image', hero);
		var title = $('.hero-title', hero);
		var social = $('.hero-social', hero);

		// start positions: photo below the slide, text and icons left of it
		function setStart() {
			var h = hero.offsetHeight;
			image.style.transform = 'translateY(' + (h - image.offsetTop) + 'px)';
			title.style.transform = 'translateX(' + -(title.offsetLeft + title.offsetWidth) + 'px)';
			social.style.transform = 'translateX(' + -(social.offsetLeft + social.offsetWidth) + 'px)';
		}
		setStart();
		hero.classList.add('is-init');

		var srcs = [hero.getAttribute('data-bg'), $('img', image).getAttribute('src')];
		var pending = srcs.length;
		function loaded() {
			pending -= 1;
			if (pending > 0) { return; }
			bg.style.backgroundImage = 'url("' + srcs[0] + '")';
			// two frames so the start position is painted before animating
			win.requestAnimationFrame(function () {
				win.requestAnimationFrame(function () {
					hero.classList.add('is-animating');
					hero.classList.add('is-ready');
					setTimeout(function () {
						hero.classList.remove('is-animating');
						image.style.transform = title.style.transform = social.style.transform = '';
					}, 2000);
				});
			});
		}
		srcs.forEach(function (src) {
			var im = new Image();
			im.onload = im.onerror = loaded;
			im.src = src;
		});
	}

	/* ------------------------------------------------------------------ */
	/* Contact form (same messages and behaviour as Contact Form 7)        */
	/* ------------------------------------------------------------------ */

	var MESSAGES = {
		mail_sent_ok: 'Bedankt voor je bericht; het is verzonden.',
		mail_sent_ng: 'Er is een fout opgetreden bij het versturen van het bericht; probeer het later nog eens.',
		validation_error: 'Een of meer velden bevatten een fout; graag controleren en opnieuw proberen.',
		spam: 'Er is een fout opgetreden bij het versturen van het bericht; probeer het later nog eens.',
		invalid_required: 'Het veld is verplicht.',
		invalid_email: 'The e-mail address entered is invalid.'
	};

	function initContactForm() {
		var form = $('.wpcf7-form');
		if (!form) { return; }
		var wrap = form.closest('.wpcf7');
		var output = $('.wpcf7-response-output', form);
		var srResponse = $('.screen-reader-response', wrap);
		var submit = $('.wpcf7-submit', form);
		var loaderEl = doc.createElement('span');
		loaderEl.className = 'ajax-loader';
		submit.parentNode.insertBefore(loaderEl, submit.nextSibling);

		// simple bot check: real browsers fill this in
		var check = $('input[name="_va_check"]', form);
		if (check) { check.value = 'ok-' + Date.now(); }

		function clearResponse() {
			form.classList.remove('invalid', 'spam', 'sent', 'failed');
			srResponse.innerHTML = '';
			srResponse.removeAttribute('role');
			$$('.wpcf7-not-valid-tip', form).forEach(function (t) { t.parentNode.removeChild(t); });
			$$('[aria-invalid]', form).forEach(function (el) { el.setAttribute('aria-invalid', 'false'); });
			$$('.wpcf7-form-control', form).forEach(function (el) { el.classList.remove('wpcf7-not-valid'); });
			output.style.display = 'none';
			output.innerHTML = '';
			output.removeAttribute('role');
			output.classList.remove('wpcf7-mail-sent-ok', 'wpcf7-mail-sent-ng', 'wpcf7-validation-errors', 'wpcf7-spam-blocked');
		}

		function notValidTip(fieldWrap, message) {
			var tip = doc.createElement('span');
			tip.setAttribute('role', 'alert');
			tip.className = 'wpcf7-not-valid-tip';
			tip.textContent = message;
			fieldWrap.appendChild(tip);
		}

		function validate() {
			var invalid = [];
			var name = form.elements['your-name'];
			var email = form.elements['email'];
			if (!name.value.trim()) { invalid.push({ into: 'your-name', message: MESSAGES.invalid_required }); }
			if (!email.value.trim()) { invalid.push({ into: 'email', message: MESSAGES.invalid_required }); }
			else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) { invalid.push({ into: 'email', message: MESSAGES.invalid_email }); }
			return invalid;
		}

		function showResponse(status, message, invalid) {
			switch (status) {
				case 'validation_failed':
					invalid.forEach(function (f) {
						var w = $('.wpcf7-form-control-wrap.' + f.into, form);
						notValidTip(w, f.message);
						$('.wpcf7-form-control', w).classList.add('wpcf7-not-valid');
						$('[aria-invalid]', w) && $('[aria-invalid]', w).setAttribute('aria-invalid', 'true');
					});
					output.classList.add('wpcf7-validation-errors');
					form.classList.add('invalid');
					break;
				case 'spam':
					output.classList.add('wpcf7-spam-blocked');
					form.classList.add('spam');
					break;
				case 'mail_sent':
					output.classList.add('wpcf7-mail-sent-ok');
					form.classList.add('sent');
					form.reset();
					if (check) { check.value = 'ok-' + Date.now(); }
					break;
				default:
					output.classList.add('wpcf7-mail-sent-ng');
					form.classList.add('failed');
			}
			output.textContent = message;
			output.setAttribute('role', 'alert');
			slideDown(output, 200);

			srResponse.textContent = message;
			if (invalid && invalid.length) {
				var ul = doc.createElement('ul');
				invalid.forEach(function (f) { var li = doc.createElement('li'); li.textContent = f.message; ul.appendChild(li); });
				srResponse.appendChild(ul);
			}
			srResponse.setAttribute('role', 'alert');
		}

		form.addEventListener('submit', function (e) {
			e.preventDefault();
			loaderEl.classList.add('is-active');
			clearResponse();
			var invalid = validate();
			var done = function (status, message, list) {
				showResponse(status, message, list || []);
				loaderEl.classList.remove('is-active');
			};
			if (invalid.length) {
				// the original validated on the server; keep a short delay so it feels the same
				setTimeout(function () { done('validation_failed', MESSAGES.validation_error, invalid); }, 300);
				return;
			}
			var data = new FormData(form);
			fetch(form.getAttribute('action'), { method: 'POST', body: data, headers: { 'Accept': 'application/json' } })
				.then(function (r) { return r.json(); })
				.then(function (res) {
					if (res.status === 'validation_failed') { done(res.status, MESSAGES.validation_error, res.invalidFields || []); }
					else if (res.status === 'mail_sent') { done('mail_sent', MESSAGES.mail_sent_ok); }
					else if (res.status === 'spam') { done('spam', MESSAGES.spam); }
					else { done('mail_failed', MESSAGES.mail_sent_ng); }
				})
				.catch(function () { done('mail_failed', MESSAGES.mail_sent_ng); });
		});
	}

	/* ------------------------------------------------------------------ */

	function ready(fn) {
		if (doc.readyState !== 'loading') { fn(); } else { doc.addEventListener('DOMContentLoaded', fn); }
	}

	ready(function () {
		initHero();
		initMobileMenu();
		initCookieNotice();
		initLightbox();
		initContactForm();
	});
})();
