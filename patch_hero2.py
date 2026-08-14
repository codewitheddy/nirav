import os

path = os.path.join('shop', 'templates', 'home.html')
with open(path, encoding='utf-8') as f:
    lines = f.readlines()

# Find the {% with b=hero_banner %} line
start = None
end = None
for i, line in enumerate(lines):
    if '{% with b=hero_banner %}' in line and start is None:
        start = i
    if start is not None and i > start and '{% endwith %}' in line:
        end = i
        break

print(f'Hero block: lines {start+1} to {end+1}')

new_hero = '''    <!-- Hero Section -->
    {% with b=hero_banner %}
    {% with bg_img=b.get_bg_image_url|default:"" if b else "" %}
    <section class="hero" id="home">
        <div class="hero-inner{% if b and b.hide_side_image %} hero-inner--full{% endif %}"
             style="{% if b and b.get_bg_image_url %}background-image:url('{{ b.get_bg_image_url }}');background-size:cover;background-position:center;{% endif %}">

            <!-- Left: content -->
            <div class="hero-content"
                 style="{% if not b or not b.get_bg_image_url %}background:{% if b and b.bg_color %}{{ b.bg_color }}{% else %}#faf7f4{% endif %};{% else %}background:rgba(0,0,0,0.35);{% endif %}{% if b and b.color_scheme == 'dark' %}color:#fff;{% endif %}">

                {% if b and b.eyebrow %}<p class="hero-eyebrow">{{ b.eyebrow }}</p>{% else %}<p class="hero-eyebrow">Timeless Beauty</p>{% endif %}

                {% if b %}<h1>{{ b.heading_html|safe }}</h1>{% else %}<h1>Timeless Elegance,<br>Crafted to Shine</h1>{% endif %}

                {% if b and b.subtitle %}
                <p class="hero-subtitle"{% if b.color_scheme == 'dark' or b.get_bg_image_url %} style="color:rgba(255,255,255,0.82)"{% endif %}>{{ b.subtitle }}</p>
                {% else %}
                <p class="hero-subtitle">Minimal jewelry for everyday confidence.</p>
                {% endif %}

                <div class="hero-features">
                    {% if b %}
                        {% for pill in b.pills %}
                        <span class="feature-pill">
                            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                            {{ pill }}
                        </span>
                        {% endfor %}
                    {% else %}
                        <span class="feature-pill">
                            <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                            Hypoallergenic
                        </span>
                        <span class="feature-pill">
                            <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/></svg>
                            Water Resistant
                        </span>
                        <span class="feature-pill">
                            <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                            Tarnish Free
                        </span>
                    {% endif %}
                </div>

                <div class="hero-buttons">
                    {% if b and b.cta_primary_text %}
                    <a href="{{ b.cta_primary_url|default:'#products' }}" class="btn-primary" style="padding:14px 32px;font-size:0.95rem;border-radius:6px;">{{ b.cta_primary_text }} &rarr;</a>
                    {% else %}
                    <a href="#products" class="btn-primary" style="padding:14px 32px;font-size:0.95rem;border-radius:6px;">Explore Collection &rarr;</a>
                    {% endif %}

                    {% if b and b.cta_secondary_text %}
                    <a href="{{ b.cta_secondary_url|default:'#' }}" class="btn-secondary" style="padding:14px 32px;font-size:0.95rem;border-radius:6px;" target="_blank">{{ b.cta_secondary_text }}</a>
                    {% else %}
                    <a href="https://wa.me/254700840182?text=Hi!%20I%20just%20saw%20your%20collection%20on%20the%20website%20and%20I%E2%80%99m%20interested%20in%20knowing%20more." onclick="trackWhatsApp()" target="_blank" class="btn-secondary" style="padding:14px 32px;font-size:0.95rem;border-radius:6px;">Contact Us</a>
                    {% endif %}
                </div>
            </div>

            <!-- Right: side image (hidden when hide_side_image is true or no image) -->
            {% if not b or not b.hide_side_image %}
            <div class="hero-image">
                {% if b and b.get_image_url %}
                <img src="{{ b.get_image_url }}" alt="{% if b.eyebrow %}{{ b.eyebrow }}{% else %}Elegant Jewellery{% endif %}" loading="eager">
                {% elif not b %}
                <img src="{% static 'images/pnw2.png' %}" alt="Elegant Jewellery Collection" loading="eager">
                {% endif %}
            </div>
            {% endif %}
        </div>

        <!-- Social proof strip -->
        <div class="hero-strip">
            <div class="hero-strip-item">
                <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                4.8/5 from 2,000+ customers
            </div>
            <div class="hero-strip-item">
                <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><rect x="1" y="3" width="15" height="13" rx="2"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
                Free Nairobi delivery over Ksh 2,000
            </div>
            <div class="hero-strip-item">
                <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                Easy WhatsApp ordering
            </div>
        </div>
    </section>
    {% endwith %}
    {% endwith %}
'''

new_lines = lines[:start] + [new_hero] + lines[end+1:]
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Hero section updated.')
