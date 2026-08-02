---
title: "Search"
description: "Search harness engineering resources"
---

<div id="search"></div>
<script>
  if (window.pagefind) {
    new pagefind.ui({ element: "#search" });
  } else {
    document.getElementById("search").innerHTML =
      "<p>Search index is generated at build time. It will be available once the site is built for production.</p>";
  }
</script>