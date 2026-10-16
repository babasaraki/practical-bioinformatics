## Shared setup for every R chapter of
## "Practical Approach to Learning Bioinformatics".
## Each R chapter begins with:  source(here::here("R", "_common.R"))
## or, when `here` is unavailable, with a relative source() call.

set.seed(20250101)

knitr::opts_chunk$set(
  comment   = "#>",
  collapse  = TRUE,
  warning   = FALSE,
  message   = FALSE,
  fig.align = "center",
  fig.width = 6,
  fig.height = 4,
  dpi       = 300,
  out.width = "90%"
)

options(
  digits = 4,
  width = 76,
  dplyr.summarise.inform = FALSE,
  tibble.print_min = 6,
  tibble.print_max = 10,
  stringsAsFactors = FALSE
)

## Locate a bundled data file from any chapter directory.
book_data <- function(...) {
  candidates <- c(file.path("data", ...), file.path("..", "data", ...),
                  file.path("..", "..", "data", ...))
  hit <- candidates[file.exists(candidates)]
  if (!length(hit)) {
    stop("bundled data file not found: ", file.path(...),
         "\nRun `python scripts/fetch_data.py` from the book root first.",
         call. = FALSE)
  }
  normalizePath(hit[1])
}

## House plotting style, used by every ggplot in the book.
if (requireNamespace("ggplot2", quietly = TRUE)) {
  ggplot2::theme_set(
    ggplot2::theme_minimal(base_size = 11) +
      ggplot2::theme(
        panel.grid.minor = ggplot2::element_blank(),
        panel.grid.major = ggplot2::element_line(colour = "grey90", linewidth = 0.3),
        strip.text = ggplot2::element_text(face = "bold"),
        plot.title = ggplot2::element_text(face = "bold", size = 12),
        plot.caption = ggplot2::element_text(colour = "grey40", size = 8),
        legend.position = "bottom"
      )
  )
}

## Qualitative palette used consistently across the book (colour-blind safe).
book_palette <- c("#1A5276", "#117864", "#B9770E", "#922B21",
                  "#6C3483", "#2E86C1", "#7D6608", "#5D6D7E")
