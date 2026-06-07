from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0004_add_group_key"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="blogpost",
            index=models.Index(
                fields=["is_published", "language"],
                name="blog_post_pub_lang_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="blogpost",
            index=models.Index(
                fields=["is_featured"],
                name="blog_post_featured_idx",
            ),
        ),
    ]
