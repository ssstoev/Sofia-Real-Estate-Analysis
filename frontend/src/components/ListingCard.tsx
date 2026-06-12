import { Listing } from "@/api/api";
import { MapPin, BedDouble, Bath, Ruler, ExternalLink } from "lucide-react";

interface ListingCardProps {
  listing: Listing;
}

const ListingCard = ({ listing }: ListingCardProps) => {
  // const formattedPrice = new Intl.NumberFormat("en-EU", {
  //   style: "currency",
  //   currency: listing.currency,
  //   maximumFractionDigits: 0,
  // }).format(listing.price);

  return (
    <div className="group flex gap-4 rounded-xl border border-border bg-card p-3 transition-shadow hover:shadow-md">
      <div className="relative h-28 w-40 flex-shrink-0 overflow-hidden rounded-lg">
        <img
          src={listing.img_url}
          // alt={listing.title}
          className="h-full w-full object-cover transition-transform group-hover:scale-105"
        />
      </div>

      <div className="flex min-w-0 flex-1 flex-col justify-between">
        <div>
          <div className="flex items-start justify-between gap-2">
            <h3 className="truncate text-sm font-semibold text-foreground">
              {listing.title}
            </h3>
            {listing.link && (
              <a
                href={listing.link}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-shrink-0 text-muted-foreground transition-colors hover:text-primary"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            )}
          </div>
          <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
            <MapPin className="h-3 w-3" />
            <span>{listing.neighbourhood}</span>
          </div>
        </div>

        <div className="flex items-end justify-between">
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <BedDouble className="h-3.5 w-3.5" /> 
              {/* {listing.bedrooms} */}
            </span>
            <span className="flex items-center gap-1">
              <Bath className="h-3.5 w-3.5" /> 
              {/* {listing.bathrooms} */}
            </span>
            <span className="flex items-center gap-1">
              <Ruler className="h-3.5 w-3.5" /> {listing.size_m2}m²
            </span>
          </div>
          <span className="text-base font-bold text-primary">
            {/* {formattedPrice} */}
          </span>
        </div>

        {/* {listing.tags && listing.tags.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {listing.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-secondary px-2 py-0.5 text-[10px] font-medium text-secondary-foreground"
              >
                {tag}
              </span>
            ))}
          </div>
        )} */}
      </div>
    </div>
  );
};

export default ListingCard;
